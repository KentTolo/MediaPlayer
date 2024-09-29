import sys
import os
import pygame
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QSlider, QFileDialog)
from PyQt6.QtCore import Qt, QTimer
from moviepy.editor import VideoFileClip

class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kent Tolo Media Player")
        self.setGeometry(200, 200, 900, 400)
        self.init_ui()

        # Initialize pygame
        pygame.init()
        self.media_player = pygame.mixer.music

        # To keep track of the current video clip
        self.media_clip = None
        self.playing = False

    def init_ui(self):
        # Color Scheme
        self.setStyleSheet("background-color: #333; color: #fff;")

        # Playlist on the left half
        self.playlist = QListWidget(self)
        self.playlist.setStyleSheet("background-color: #555;")

        # Add Media button below the playlist
        self.add_media_button = QPushButton('Add Media', self)
        self.add_media_button.setStyleSheet("background-color: #555; padding: 10px; font-size: 16px;")
        self.add_media_button.clicked.connect(self.add_media)

        # Right half: media currently playing
        self.current_media_label = QLabel("No media playing", self)
        self.current_media_label.setStyleSheet("font-size: 18px;")
        self.current_media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        # Slider for media progress
        self.progress_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self.set_position)

        # Control buttons layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.next_button)

        # Add Media and playlist layout (Left half)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.playlist)
        left_layout.addWidget(self.add_media_button)

        # Right half layout: Current media display + progress bar + controls
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.current_media_label)
        right_layout.addWidget(self.progress_slider)
        right_layout.addLayout(controls_layout)

        # Combine both halves
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)  # Left: playlist & add media button
        main_layout.addLayout(right_layout, 2)  # Right: current media & controls

        self.setLayout(main_layout)

        # Timer for updating the progress bar
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # Update every second
        self.timer.timeout.connect(self.update_progress)

        self.media_files = []
        self.current_media_index = -1

    def add_media(self):
        media_files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", "Media Files (*.mp4 *.avi *.mp3)")
        if media_files:
            self.media_files.extend(media_files)
            self.playlist.addItems([os.path.basename(file) for file in media_files])

    def play_media(self):
        if self.playlist.currentRow() >= 0:
            self.current_media_index = self.playlist.currentRow()
            self.load_media(self.media_files[self.current_media_index])

    def pause_media(self):
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
            self.pause_button.setText("Resume")  # Change button to Resume
        else:
            pygame.mixer.music.unpause()
            self.playing = True
            self.pause_button.setText("Pause")  # Change button back to Pause

    def stop_media(self):
        self.playing = False
        self.timer.stop()
        pygame.mixer.music.stop()
        self.current_media_label.setText("Stopped")
        self.progress_slider.setValue(0)

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

        # Reset the progress slider
        self.progress_slider.setValue(0)

        if media_path.endswith(('.mp4', '.avi')):
            self.media_clip = VideoFileClip(media_path)
            self.playing = True
            self.timer.start()
            self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
            pygame.mixer.music.load(media_path)  # Load the video file for audio
            pygame.mixer.music.play()
            self.progress_slider.setMaximum(int(self.media_clip.duration))  # Set the max value to video duration
        elif media_path.endswith('.mp3'):
            self.media_clip = None  # No video clip for audio files
            pygame.mixer.music.load(media_path)
            pygame.mixer.music.play()
            self.playing = True
            self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
            self.progress_slider.setMaximum(int(pygame.mixer.Sound(media_path).get_length()))  # Set the max value to audio duration

    def update_progress(self):
        if self.playing:
            if self.media_clip:
                # Update progress bar for video
                current_time = self.media_clip.reader.time
                self.progress_slider.setValue(int(current_time))
                if current_time >= self.media_clip.duration:
                    self.stop_media()
            else:  # For audio
                current_time = pygame.mixer.music.get_pos() / 1000  # Convert milliseconds to seconds
                self.progress_slider.setValue(int(current_time))

    def set_position(self, position):
        if self.media_clip:
            self.media_clip.reader.seek(position)
        pygame.mixer.music.set_pos(position)  # This may need handling depending on pygame's version

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec())
