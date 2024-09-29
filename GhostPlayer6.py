import sys
import os
import pygame
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QSlider, QFileDialog)
from PyQt6.QtCore import Qt, QTimer
from moviepy.editor import VideoFileClip
import numpy as np
from PyQt6.QtGui import QImage, QPixmap

class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kent Tolo Media Player")
        self.setGeometry(200, 200, 900, 400)
        self.init_ui()

        # Initialize pygame for audio playback
        pygame.mixer.init()
        pygame.init()

        self.media_clip = None
        self.playing = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # Update every second
        self.timer.timeout.connect(self.update_progress)

    def init_ui(self):
        # Style updated to match the theme, including the title section
        self.setStyleSheet("""
            background-color: #333;
            color: #fff;
            font-size: 14px;
            font-family: Arial, Helvetica, sans-serif;
        """)
        
        self.playlist = QListWidget(self)
        self.playlist.setStyleSheet("background-color: #555;")

        self.add_media_button = QPushButton('Add Media', self)
        self.add_media_button.clicked.connect(self.add_media)
        self.remove_media_button = QPushButton('Remove Media', self)
        self.remove_media_button.clicked.connect(self.remove_media)
        
        self.current_media_label = QLabel("No media playing", self)
        self.current_media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.video_label = QLabel(self)
        self.video_label.setScaledContents(True)  # Allow dynamic scaling of video

        # Control buttons
        self.play_button = QPushButton('Play', self)
        self.play_button.clicked.connect(self.play_media)

        self.pause_button = QPushButton('Pause', self)
        self.pause_button.clicked.connect(self.pause_media)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_media)

        self.previous_button = QPushButton('Previous', self)
        self.previous_button.clicked.connect(self.previous_media)

        self.next_button = QPushButton('Next', self)
        self.next_button.clicked.connect(self.next_media)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self.set_position)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.next_button)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.playlist)
        left_layout.addWidget(self.add_media_button)
        left_layout.addWidget(self.remove_media_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.current_media_label)
        right_layout.addWidget(self.video_label)
        right_layout.addWidget(self.progress_slider)
        right_layout.addLayout(controls_layout)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

        self.media_files = []
        self.current_media_index = -1

    def add_media(self):
        media_files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", "Media Files (*.mp4 *.avi *.mp3)")
        if media_files:
            self.media_files.extend(media_files)
            self.playlist.addItems([os.path.basename(file) for file in media_files])

    def remove_media(self):
        selected_row = self.playlist.currentRow()
        if selected_row >= 0:
            del self.media_files[selected_row]
            self.playlist.takeItem(selected_row)

    def play_media(self):
        if self.playlist.currentRow() >= 0:
            self.current_media_index = self.playlist.currentRow()
            self.load_media(self.media_files[self.current_media_index])

    def pause_media(self):
        if self.playing:
            self.timer.stop()
            if self.media_clip:
                self.media_clip.reader.close()
            pygame.mixer.music.pause()
            self.playing = False
            self.pause_button.setText("Resume")
        else:
            self.playing = True
            self.current_media_label.setText(f"Playing: {os.path.basename(self.media_files[self.current_media_index])}")
            self.timer.start()
            self.update_video_frame()
            pygame.mixer.music.unpause()

    def stop_media(self):
        self.playing = False
        self.timer.stop()
        self.current_media_label.setText("Stopped")
        self.progress_slider.setValue(0)
        self.video_label.clear()
        if self.media_clip:
            self.media_clip.reader.close()
            self.media_clip = None
        pygame.mixer.music.stop()

    def previous_media(self):
        if self.current_media_index > 0:
            self.current_media_index -= 1
            self.load_media(self.media_files[self.current_media_index])

    def next_media(self):
        if self.current_media_index < len(self.media_files) - 1:
            self.current_media_index += 1
            self.load_media(self.media_files[self.current_media_index])

    def load_media(self, media_path):
        if not os.path.exists(media_path):
            print(f"Error: File not found: {media_path}")
            return

        self.progress_slider.setValue(0)

        if media_path.endswith(('.mp4', '.avi')):
            try:
                self.media_clip = VideoFileClip(media_path)
                self.playing = True
                self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
                self.progress_slider.setMaximum(int(self.media_clip.duration))
                self.timer.start()
                self.update_video_frame()
            except Exception as e:
                print(f"Error loading video: {e}")
                self.current_media_label.setText("Error loading video.")
        elif media_path.endswith('.mp3'):
            try:
                pygame.mixer.music.load(media_path)
                pygame.mixer.music.play()
                self.playing = True
                self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
                audio_length = pygame.mixer.Sound(media_path).get_length()
                self.progress_slider.setMaximum(int(audio_length))
                self.timer.start()
            except Exception as e:
                print(f"Error loading audio: {e}")
                self.current_media_label.setText("Error loading audio.")

    def update_progress(self):
        if self.playing:
            if self.media_clip:  # For video
                current_time = self.media_clip.reader.pos
                self.progress_slider.setValue(int(current_time))
                if current_time >= self.media_clip.duration:
                    self.stop_media()
                self.update_video_frame()
            else:  # For audio
                current_time = pygame.mixer.music.get_pos() // 1000
                self.progress_slider.setValue(current_time)
                if current_time >= self.progress_slider.maximum():
                    self.stop_media()

    def update_video_frame(self):
        if self.playing and self.media_clip:
            try:
                frame = self.media_clip.get_frame(self.media_clip.reader.pos)
                if frame is not None:
                    frame = np.array(frame)
                    height, width, channel = frame.shape
                    bytes_per_line = 3 * width
                    q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                    
                    # Dynamically resize video to fit QLabel
                    pixmap = QPixmap.fromImage(q_img).scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
                    self.video_label.setPixmap(pixmap)

                    QTimer.singleShot(33, self.update_video_frame)  # Schedule the next frame update
            except Exception as e:
                print(f"Error updating video frame: {e}")

    def set_position(self, position):
        if self.media_clip:
            self.media_clip.reader.seek(position)
        else:  # For audio
            pygame.mixer.music.set_pos(position)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec())
