import sys
import os
import pygame
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from moviepy.editor import VideoFileClip, AudioFileClip
import numpy as np
from PyQt6.QtGui import QImage, QPixmap
import time


class VideoThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, video_clip):
        super().__init__()
        self.video_clip = video_clip
        self.running = True
        self.paused = False
        self.current_time = 0
        self.last_frame_time = 0

    def run(self):
        while self.running:
            if not self.paused:
                current_time = time.time()
                frame_interval = 1 / self.video_clip.fps

                if current_time - self.last_frame_time >= frame_interval:
                    try:
                        frame = self.video_clip.get_frame(self.current_time)
                        self.frame_ready.emit(frame)
                        self.current_time += frame_interval
                        self.last_frame_time = current_time

                        if self.current_time >= self.video_clip.duration:
                            self.running = False
                    except Exception as e:
                        print(f"Error getting frame: {e}")
                        self.running = False
                else:
                    time.sleep(0.001)
            else:
                time.sleep(0.01)

    def stop(self):
        self.running = False
        self.wait()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def seek(self, time_pos):
        self.current_time = time_pos
        self.last_frame_time = 0


class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Player")
        self.setGeometry(200, 200, 900, 600)
        self.init_ui()

        pygame.mixer.init()
        pygame.init()

        self.media_clip = None
        self.audio_clip = None  # For audio playback in video
        self.video_thread = None
        self.playing = False
        self.paused = False
        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(1000)
        self.progress_timer.timeout.connect(self.update_progress)

        self.media_files = []
        self.current_media_index = -1

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #333333;
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #555555;
                border: none;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QListWidget {
                background-color: #444444;
                border: none;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #666666;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                margin: -2px 0;
            }
        """)

        # Create widgets
        self.playlist = QListWidget(self)
        self.add_media_button = QPushButton('Add Media', self)
        self.remove_media_button = QPushButton('Remove Media', self)
        self.current_media_label = QLabel("No media playing", self)
        self.video_label = QLabel(self)
        self.video_label.setMinimumSize(400, 300)
        self.play_button = QPushButton('Play', self)
        self.pause_button = QPushButton('Pause', self)
        self.stop_button = QPushButton('Stop', self)
        self.previous_button = QPushButton('Previous', self)
        self.next_button = QPushButton('Next', self)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal, self)

        # Connect signals
        self.add_media_button.clicked.connect(self.add_media)
        self.remove_media_button.clicked.connect(self.remove_media)
        self.play_button.clicked.connect(self.play_media)
        self.pause_button.clicked.connect(self.pause_media)
        self.stop_button.clicked.connect(self.stop_media)
        self.previous_button.clicked.connect(self.previous_media)
        self.next_button.clicked.connect(self.next_media)
        self.progress_slider.sliderMoved.connect(self.set_position)

        # Set up layouts
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()

        # Add widgets to layouts
        left_layout.addWidget(self.playlist)
        left_layout.addWidget(self.add_media_button)
        left_layout.addWidget(self.remove_media_button)

        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.next_button)

        right_layout.addWidget(self.current_media_label)
        right_layout.addWidget(self.video_label)
        right_layout.addWidget(self.progress_slider)
        right_layout.addLayout(controls_layout)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

    def add_media(self):
        file_filter = "Media Files (*.mp4 *.avi *.mp3);;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", file_filter)
        for file in files:
            self.media_files.append(file)
            self.playlist.addItem(os.path.basename(file))

    def remove_media(self):
        current_row = self.playlist.currentRow()
        if current_row >= 0:
            self.playlist.takeItem(current_row)
            del self.media_files[current_row]
            if self.current_media_index == current_row:
                self.stop_media()

    def play_media(self):
        if not self.playing:
            selected_row = self.playlist.currentRow()
            if selected_row >= 0:
                self.current_media_index = selected_row
                self.load_media(self.media_files[self.current_media_index])

    def load_media(self, media_path):
        self.stop_media()

        if not os.path.exists(media_path):
            print(f"Error: File not found: {media_path}")
            self.current_media_label.setText("Error loading media")
            return

        self.progress_slider.setValue(0)

        try:
            if media_path.lower().endswith(('.mp4', '.avi')):
                # For video with audio
                self.media_clip = VideoFileClip(media_path)
                self.audio_clip = self.media_clip.audio  # Extract audio from video

                self.playing = True
                self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
                self.progress_slider.setMaximum(int(self.media_clip.duration))

                # Start video playback in a separate thread
                self.video_thread = VideoThread(self.media_clip)
                self.video_thread.frame_ready.connect(self.update_video_frame)
                self.video_thread.start()

                # Start progress timer
                self.progress_timer.start()

                # Play video audio
                if self.audio_clip:
                    self.audio_clip.preview(fps=44100)

            elif media_path.lower().endswith('.mp3'):
                # For audio files
                pygame.mixer.music.load(media_path)
                pygame.mixer.music.play()
                self.playing = True
                self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
                sound = pygame.mixer.Sound(media_path)
                self.progress_slider.setMaximum(int(sound.get_length()))
                self.progress_timer.start()

        except Exception as e:
            print(f"Error loading media: {e}")
            self.current_media_label.setText("Error loading media")

    def update_video_frame(self, frame):
        try:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)

            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error updating video frame: {e}")

    def update_progress(self):
        if self.playing and not self.paused:
            current_value = self.progress_slider.value() + 1
            if current_value <= self.progress_slider.maximum():
                self.progress_slider.setValue(current_value)
            else:
                self.stop_media()

    def set_position(self, position):
        self.progress_slider.setValue(position)
        if self.media_clip:
            if isinstance(self.media_clip, VideoFileClip):
                self.video_thread.seek(position)

    def pause_media(self):
        if self.playing:
            if not self.paused:
                if isinstance(self.media_clip, VideoFileClip) and self.audio_clip:
                    self.audio_clip.preview(fps=44100)  # Continue audio
                self.video_thread.pause()
                self.paused = True
                self.pause_button.setText("Resume")
            else:
                self.video_thread.resume()
                self.paused = False
                self.pause_button.setText("Pause")

    def stop_media(self):
        if self.playing:
            self.playing = False
            self.paused = False
            self.pause_button.setText("Pause")
            self.current_media_label.setText("No media playing")
            self.progress_timer.stop()

            if self.video_thread:
                self.video_thread.stop()
                self.video_label.clear()

    def previous_media(self):
        if self.current_media_index > 0:
            self.current_media_index -= 1
            self.load_media(self.media_files[self.current_media_index])

    def next_media(self):
        if self.current_media_index < len(self.media_files) - 1:
            self.current_media_index += 1
            self.load_media(self.media_files[self.current_media_index])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec())
