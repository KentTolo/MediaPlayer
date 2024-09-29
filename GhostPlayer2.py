import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider)
from PyQt6.QtCore import Qt, QTimer
from moviepy.editor import VideoFileClip
import os
import pygame

class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kent Tolo Media Player")
        self.setGeometry(200, 200, 900, 400)
        self.init_ui()

        # Initialize pygame
        pygame.init()
        self.media_player = pygame.mixer.music
        self.screen = pygame.display.set_mode((640, 480))  # Adjust dimensions as needed

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
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_progress)

        self.media_files = []
        self.current_media_index = -1
        self.media_clip = None
        self.playing = False

    def add_media(self):
        from PyQt6.QtWidgets import QFileDialog
        file_dialog = QFileDialog()
        media_files, _ = file_dialog.getOpenFileNames(self, "Select Media Files", "", "Media Files (*.mp4 *.avi *.mp3)")
        if media_files:
            self.media_files.extend(media_files)
            self.playlist.addItems([os.path.basename(file) for file in media_files])

    def play_media(self):
        if self.playlist.currentRow() >= 0:
            self.current_media_index = self.playlist.currentRow()
            self.load_media(self.media_files[self.current_media_index])

    def pause_media(self):
        if self.playing:
            if self.media_player:
                self.media_player.pause()
            self.playing = False

    def stop_media(self):
        self.playing = False
        self.timer.stop()
        if self.media_player:
            self.media_player.stop()
        if self.media_clip:
            self.media_clip.close()
        self.current_media_label.setText("Stopped")

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

        if media_path.endswith('.mp4') or media_path.endswith('.avi'):
            self.media_clip = VideoFileClip(media_path)
            self.video_surface = pygame.image.load(media_path)
            self.playing = True
            self.timer.start()
        elif media_path.endswith('.mp3'):
            self.media_player.load(media_path)
            self.media_player.play()
            self.playing = True

        self.current_media_label.setText(f"Playing: {os.path.basename(media_path)}")
        self.progress_slider.setMaximum(int(self.media_clip.duration)) if self.media_clip else 0

    def update_progress(self):
        if self.playing:
            if self.media_clip:
                current_time = self.media_clip.reader.time
                self.progress_slider.setValue(int(current_time))
                if current_time >= self.media_clip.duration:
                    self.stop_media()
            elif self.media_player:
                current_time = self.media_player.get_pos() / 1000
                self.progress_slider.setValue(int(current_time))
                if current_time >= self.media_player.get_length() / 1000:
                    self.stop_media()

    def set_position(self, position):
        if self.media_clip:
            self.media_clip.seek(position)

    def video_loop(self):
        while self.playing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.playing = False
                    pygame.quit()
                    sys.exit()

            if self.media_clip:
                self.screen.blit(self.video_surface, (0, 0))
                pygame.display.flip()
                self.media_clip.seek(self.progress_slider.value())

            self.video_clock.tick(30)  # Adjust FPS as needed

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec())