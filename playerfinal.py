import sys
import os
import pygame
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from moviepy.editor import VideoFileClip
import numpy as np
from PyQt6.QtGui import QImage, QPixmap
import time
import threading

class VideoThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    position_updated = pyqtSignal(float)
    playback_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.video_clip = None
        self.audio_thread = None
        self.running = False
        self.paused = False
        self.current_time = 0
        self.fps = 0
        self.start_time = 0
        self.lock = threading.Lock()

    def set_video(self, video_path):
        with self.lock:
            if self.video_clip:
                self.stop()
            try:
                self.video_clip = VideoFileClip(video_path)
                self.fps = self.video_clip.fps
                self.current_time = 0
                return True
            except Exception as e:
                print(f"Error loading video: {e}")
                return False

    def run(self):
        with self.lock:
            if not self.video_clip:
                return
            self.running = True
            self.start_time = time.time() - (self.current_time if self.paused else 0)

        if self.video_clip.audio:
            self.audio_thread = threading.Thread(target=self.play_audio)
            self.audio_thread.start()
        
        while self.running:
            with self.lock:
                if self.paused:
                    self.msleep(10)
                    continue

                if not self.video_clip:
                    break

                try:
                    elapsed_time = time.time() - self.start_time
                    self.current_time = elapsed_time
                    
                    if self.current_time >= self.video_clip.duration:
                        self.running = False
                        self.playback_finished.emit()
                        break
                    
                    frame = self.video_clip.get_frame(self.current_time)
                    self.frame_ready.emit(frame)
                    self.position_updated.emit(self.current_time)
                    
                    next_frame_time = (self.current_time + 1/self.fps)
                    sleep_time = max(0, (next_frame_time - elapsed_time))
                    self.msleep(int(sleep_time * 1000))
                    
                except Exception as e:
                    print(f"Error in video playback: {e}")
                    self.running = False
                    break

    def play_audio(self):
        try:
            self.video_clip.audio.preview()
        except Exception as e:
            print(f"Error playing audio: {e}")

    def stop(self):
        with self.lock:
            self.running = False
            self.paused = False
        
        if self.audio_thread and self.audio_thread.is_alive():
            pygame.mixer.quit()
            pygame.mixer.init()
            self.audio_thread.join(timeout=1)
        
        self.wait()
        
        with self.lock:
            if self.video_clip:
                try:
                    self.video_clip.close()
                except Exception as e:
                    print(f"Error closing video clip: {e}")
                self.video_clip = None
            self.current_time = 0

    def pause(self):
        with self.lock:
            if self.running and not self.paused:
                self.paused = True
                pygame.mixer.pause()

    def resume(self):
        with self.lock:
            if self.running and self.paused:
                self.paused = False
                self.start_time = time.time() - self.current_time
                pygame.mixer.unpause()

    def seek(self, time_pos):
        with self.lock:
            if self.video_clip:
                was_paused = self.paused
                self.stop()
                self.current_time = min(max(time_pos, 0), self.video_clip.duration)
                self.paused = was_paused
                self.running = True
                self.start()

class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Player")
        self.setGeometry(200, 200, 900, 600)
        self.init_ui()

        pygame.mixer.init()
        pygame.init()

        self.video_thread = VideoThread()
        self.video_thread.frame_ready.connect(self.update_video_frame)
        self.video_thread.position_updated.connect(self.update_slider_position)
        self.video_thread.playback_finished.connect(self.on_playback_finished)

        self.playing = False
        self.is_video = False
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
        try:
            file_filter = "Media Files (*.mp4 *.avi *.mp3);;All Files (*.*)"
            files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", file_filter)
            for file in files:
                self.media_files.append(file)
                self.playlist.addItem(os.path.basename(file))
        except Exception as e:
            print(f"Error adding media: {e}")

    def remove_media(self):
        try:
            current_row = self.playlist.currentRow()
            if current_row >= 0:
                if self.current_media_index == current_row:
                    self.stop_media()
                self.playlist.takeItem(current_row)
                del self.media_files[current_row]
                if self.current_media_index >= current_row:
                    self.current_media_index = max(-1, self.current_media_index - 1)
        except Exception as e:
            print(f"Error removing media: {e}")

    def play_media(self):
        try:
            if not self.playing:
                selected_row = self.playlist.currentRow()
                if selected_row >= 0:
                    self.current_media_index = selected_row
                    self.load_media(self.media_files[self.current_media_index])
        except Exception as e:
            print(f"Error playing media: {e}")

    def load_media(self, media_path):
        try:
            self.stop_media()

            if not os.path.exists(media_path):
                raise FileNotFoundError(f"File not found: {media_path}")

            if media_path.lower().endswith(('.mp4', '.avi')):
                self.is_video = True
                if self.video_thread.set_video(media_path):
                    duration = self.video_thread.video_clip.duration
                    self.progress_slider.setMaximum(int(duration * 1000))
                    self.video_thread.running = True
                    self.video_thread.start()
                    self.playing = True
                else:
                    raise Exception("Failed to load video")
            else:
                self.is_video = False
                pygame.mixer.music.load(media_path)
                pygame.mixer.music.play()
                sound = pygame.mixer.Sound(media_path)
                self.progress_slider.setMaximum(int(sound.get_length() * 1000))
                self.playing = True

            self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
        except Exception as e:
            print(f"Error loading media: {e}")
            self.current_media_label.setText("Error loading media")
            self.playing = False

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

    def update_slider_position(self, position):
        try:
            self.progress_slider.setValue(int(position * 1000))
        except Exception as e:
            print(f"Error updating slider position: {e}")

    def set_position(self, position):
        try:
            if self.is_video:
                self.video_thread.seek(position / 1000)
            else:
                pygame.mixer.music.set_pos(position / 1000)
        except Exception as e:
            print(f"Error setting position: {e}")

    def pause_media(self):
        try:
            if self.playing:
                if self.is_video:
                    if self.video_thread.paused:
                        self.video_thread.resume()
                        self.pause_button.setText("Pause")
                    else:
                        self.video_thread.pause()
                        self.pause_button.setText("Resume")
                else:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                        self.pause_button.setText("Resume")
                    else:
                        pygame.mixer.music.unpause()
                        self.pause_button.setText("Pause")
        except Exception as e:
            print(f"Error toggling pause: {e}")

    def stop_media(self):
        try:
            if self.playing:
                self.playing = False
                if self.is_video:
                    self.video_thread.stop()
                    self.video_label.clear()
                else:
                    pygame.mixer.music.stop()
                self.current_media_label.setText("No media playing")
                self.progress_slider.setValue(0)
                self.pause_button.setText("Pause")
        except Exception as e:
            print(f"Error stopping media: {e}")

    def previous_media(self):
        try:
            if self.current_media_index > 0:
                self.current_media_index -= 1
                self.playlist.setCurrentRow(self.current_media_index)
                self.load_media(self.media_files[self.current_media_index])
        except Exception as e:
            print(f"Error playing previous media: {e}")

    def next_media(self):
        try:
            if self.current_media_index < len(self.media_files) - 1:
                self.current_media_index += 1
                self.playlist.setCurrentRow(self.current_media_index)
                self.load_media(self.media_files[self.current_media_index])
        except Exception as e:
            print(f"Error playing next media: {e}")

    def on_playback_finished(self):
        self.next_media()

    def closeEvent(self, event):
        try:
            self.stop_media()
            event.accept()
        except Exception as e:
            print(f"Error during close: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec())