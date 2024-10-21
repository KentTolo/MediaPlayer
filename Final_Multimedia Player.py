import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QFileDialog, QStyle, QSizePolicy)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

class ImprovedMediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CS5430 Media Player")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(self.get_style_sheet())
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.init_ui()
        
        self.media_files = []
        self.current_media_index = -1
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_position)
        self.update_timer.start(1000)
        
        self.media_player.playbackStateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

    def init_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        # Playlist
        self.playlist = QListWidget(self)
        self.add_media_button = QPushButton('Add Media', self)
        self.remove_media_button = QPushButton('Remove Media', self)
        
        left_layout.addWidget(self.playlist)
        left_layout.addWidget(self.add_media_button)
        left_layout.addWidget(self.remove_media_button)
        
        # Video Widget
        self.video_widget = QVideoWidget(self)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Controls
        control_layout = QHBoxLayout()
        self.play_button = QPushButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.previous_button = QPushButton(self)
        self.previous_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.next_button = QPushButton(self)
        self.next_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.stop_button = QPushButton(self)
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)

        #Size adjustments
        control_layout.setSpacing(5)  
        self.play_button.setFixedSize(30, 30)
        self.previous_button.setFixedSize(30, 30)
        self.next_button.setFixedSize(30, 30)
        self.stop_button.setFixedSize(30, 30)


        control_layout.addWidget(self.previous_button)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.next_button)
        control_layout.addWidget(self.volume_slider)
        
        # Slider and duration
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.duration_label = QLabel("00:00 / 00:00")
        
        # Right layout
        right_layout.addWidget(self.video_widget)
        right_layout.addWidget(self.position_slider)
        right_layout.addWidget(self.duration_label)
        right_layout.addLayout(control_layout)
        
        # Main layout
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.add_media_button.clicked.connect(self.add_media)
        self.remove_media_button.clicked.connect(self.remove_media)
        self.play_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.previous_button.clicked.connect(self.previous_media)
        self.next_button.clicked.connect(self.next_media)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.playlist.itemDoubleClicked.connect(self.playlist_double_clicked)

    def add_media(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add Media", "", "Media Files (*.mp3 *.mp4 *.avi *.mkv *.wav)")
        for file in files:
            self.media_files.append(file)
            self.playlist.addItem(os.path.basename(file))

    def remove_media(self):
        current_row = self.playlist.currentRow()
        if current_row >= 0:
            self.playlist.takeItem(current_row)
            del self.media_files[current_row]
            if self.current_media_index == current_row:
                self.stop()
                self.current_media_index = -1

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            if self.current_media_index == -1 and self.playlist.count() > 0:
                self.current_media_index = 0
                self.play_media(self.current_media_index)
            else:
                self.media_player.play()

    def stop(self):
        self.media_player.stop()
        self.position_slider.setValue(0)
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def previous_media(self):
        if self.current_media_index > 0:
            self.current_media_index -= 1
            self.play_media(self.current_media_index)

    def next_media(self):
        if self.current_media_index < len(self.media_files) - 1:
            self.current_media_index += 1
            self.play_media(self.current_media_index)

    def playlist_double_clicked(self, item):
        self.current_media_index = self.playlist.row(item)
        self.play_media(self.current_media_index)

    def play_media(self, index):
        if 0 <= index < len(self.media_files):
            self.media_player.setSource(QUrl.fromLocalFile(self.media_files[index]))
            self.media_player.play()
            self.playlist.setCurrentRow(index)

    def media_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_duration_label()

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_duration_label()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_position(self):
        self.position_changed(self.media_player.position())

    def update_duration_label(self):
        position = self.media_player.position()
        duration = self.media_player.duration()
        self.duration_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100)

    @staticmethod
    def format_time(ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    @staticmethod
    def get_style_sheet():
        return """
        QWidget {
        background-color: #f5f5f5;  
        color: #333333;  
        font-size: 14px;
        }
        QPushButton {
        background-color: #87cefa;  
        color: #ffffff;
        border: none;
        padding: 8px;
        min-width: 80px;
        border-radius: 5px;
        font-weight: bold; 
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);  
        }
        QPushButton:hover {
        background-color: #76bcd9;  
        box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.2); 
        }
        QListWidget {
        background-color: #ffffff; 
        border: 1px solid #b0c4de;
        border-radius: 5px;
        color: #333333; 
        }
        QSlider::groove:horizontal {
        background: linear-gradient(to right, #87cefa, #76bcd9);  
        border: none;
        height: 8px;
        margin: 2px 0;
        border-radius: 4px;
        }
        QSlider::handle:horizontal {
        background: #ffffff;
        border: 2px solid #76bcd9;  
        width: 18px;
        margin: -2px 0;
        border-radius: 50%;  
        box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);  
        }
        QLabel {
        color: #333333;  
        font-weight: 500; 
        }
        """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = ImprovedMediaPlayer()
    player.show()
    sys.exit(app.exec())