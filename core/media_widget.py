from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QIcon
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import os


class MediaWidget(QGraphicsWidget):
    """Widget gráfico para exibir mídia (áudio, vídeo, imagem)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.playlist = []
        self.current_index = 0
        
        # Layout para controles
        layout = QVBoxLayout()
        
        # Display de vídeo
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.next_btn = QPushButton("⏭")
        
        self.prev_btn.clicked.connect(self.previous_media)
        self.play_btn.clicked.connect(self.toggle_play)
        self.next_btn.clicked.connect(self.next_media)
        
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        
        # Slider de progresso
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.seek)
        controls_layout.addWidget(self.slider)
        
        # Label de tempo
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        self.setLayout(layout)
        
        # Conectar sinais
        self.media_player.positionChanged.connect(self.update_slider)
        self.media_player.durationChanged.connect(self.update_duration)
    
    def add_media(self, file_path):
        """Adiciona mídia à playlist"""
        self.playlist.append(file_path)
        if len(self.playlist) == 1:
            self.play_media(0)
    
    def play_media(self, index):
        """Reproduz mídia no índice especificado"""
        if 0 <= index < len(self.playlist):
            self.current_index = index
            url = QUrl.fromLocalFile(self.playlist[index])
            self.media_player.setSource(url)
            self.media_player.play()
    
    def toggle_play(self):
        """Alterna entre play e pause"""
        if self.media_player.isPlaying():
            self.media_player.pause()
            self.play_btn.setText("▶")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸")
    
    def previous_media(self):
        """Próxima mídia"""
        if self.current_index > 0:
            self.play_media(self.current_index - 1)
    
    def next_media(self):
        """Próxima mídia"""
        if self.current_index < len(self.playlist) - 1:
            self.play_media(self.current_index + 1)
    
    def seek(self, position):
        """Busca posição na mídia"""
        self.media_player.setPosition(position)
    
    def update_slider(self):
        """Atualiza slider de progresso"""
        position = self.media_player.position()
        self.slider.setValue(position)
        self.update_time_label()
    
    def update_duration(self, duration):
        """Atualiza duração da mídia"""
        self.slider.setMaximum(duration)
    
    def update_time_label(self):
        """Atualiza label de tempo"""
        position = self.media_player.position()
        duration = self.media_player.duration()
        
        pos_min = position // 60000
        pos_sec = (position % 60000) // 1000
        dur_min = duration // 60000
        dur_sec = (duration % 60000) // 1000
        
        self.time_label.setText(f"{pos_min:02d}:{pos_sec:02d} / {dur_min:02d}:{dur_sec:02d}")
    
    def get_playlist(self):
        """Retorna a playlist"""
        return self.playlist
    
    def set_playlist(self, playlist):
        """Define a playlist"""
        self.playlist = playlist
        self.current_index = 0
        if self.playlist:
            self.play_media(0)
