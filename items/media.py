from PySide6.QtWidgets import QGraphicsObject, QWidget, QHBoxLayout, QPushButton, QLabel, QGraphicsProxyWidget, QVBoxLayout, QMenu, QFileDialog, QSlider, QGraphicsDropShadowEffect
from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QPixmap, QImage, QPainter, QAction, QColor
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QMovie
from .shapes import Handle
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import QApplication


class ReplaceItemCommand(QUndoCommand):
    def __init__(self, scene, old_item, new_item, description="Substituir mídia"):
        super().__init__(description)
        self.scene = scene
        self.old_item = old_item
        self.new_item = new_item
        self._rewired = []  # list of (conn, 'source'|'target')

    def redo(self):
        # Rewire connections to new_item
        try:
            from core.connection import SmartConnection
            for it in list(self.scene.items()):
                if isinstance(it, SmartConnection):
                    if it.source is self.old_item:
                        it.source = self.new_item
                        self._rewired.append((it, 'source'))
                        it.update_path()
                    if it.target is self.old_item:
                        it.target = self.new_item
                        self._rewired.append((it, 'target'))
                        it.update_path()
        except Exception:
            pass
        if self.old_item.scene():
            self.scene.removeItem(self.old_item)
        if not self.new_item.scene():
            self.scene.addItem(self.new_item)

    def undo(self):
        # Rewire connections back to old_item
        try:
            for conn, side in self._rewired:
                if side == 'source' and conn.source is self.new_item:
                    conn.source = self.old_item
                    conn.update_path()
                if side == 'target' and conn.target is self.new_item:
                    conn.target = self.old_item
                    conn.update_path()
        except Exception:
            pass
        if self.new_item.scene():
            self.scene.removeItem(self.new_item)
        if not self.old_item.scene():
            self.scene.addItem(self.old_item)

class MediaItem(QGraphicsObject):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(6, 6)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def paint(self, painter, option, widget=None):
        pass

    def _replace_self(self, new_item, description="Substituir mídia"):
        sc = self.scene()
        if sc is None:
            return
        win = QApplication.activeWindow()
        try:
            if hasattr(win, 'undo_stack') and win.undo_stack is not None:
                cmd = ReplaceItemCommand(sc, self, new_item, description)
                win.undo_stack.push(cmd)
                return
        except Exception:
            pass
        pos = self.pos()
        new_item.setPos(pos)
        sc.addItem(new_item)
        sc.removeItem(self)


class MediaImageItem(MediaItem):
    def __init__(self, image: QImage, source: str = "", parent: QObject = None):
        super().__init__(parent)
        self._movie = None
        self._pix = QPixmap.fromImage(image) if not image.isNull() else QPixmap()
        # Tentar inicializar QMovie para GIF/WEBP quando source é arquivo local
        try:
            if source and isinstance(source, str):
                low = source.lower()
                if low.endswith((".gif", ".webp")):
                    mv = QMovie(source)
                    if mv.isValid():
                        self._movie = mv
                        self._movie.frameChanged.connect(self.update)
                        self._movie.start()
                        if not self._pix or self._pix.isNull():
                            self._pix = self._movie.currentPixmap()
        except Exception:
            pass

        w = max(40, self._pix.width() or 40)
        h = max(40, self._pix.height() or 40)
        self._rect = QRectF(0, 0, w, h)
        self.source = source
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)

        self.handles = {
            'tl': Handle(self, 'tl'),
            'tr': Handle(self, 'tr'),
            'bl': Handle(self, 'bl'),
            'br': Handle(self, 'br'),
        }
        self._update_handle_positions()
        self._set_handles_visible(False)

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        target = self._rect.toRect()
        if self._movie is not None:
            frame = self._movie.currentPixmap()
            if not frame.isNull():
                painter.drawPixmap(target, frame.scaled(target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif not self._pix.isNull():
            painter.drawPixmap(target, self._pix.scaled(
                target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def _update_handle_positions(self):
        r = self._rect
        w, h = r.width(), r.height()
        self.handles['tl'].setPos(0, 0)
        self.handles['tr'].setPos(w, 0)
        self.handles['bl'].setPos(0, h)
        self.handles['br'].setPos(w, h)

    def _set_handles_visible(self, visible: bool):
        for h in self.handles.values():
            h.setVisible(visible)

    def resize_from_corner(self, corner: str, scene_pos):
        self.prepareGeometryChange()
        local = self.mapFromScene(scene_pos)
        r = self._rect
        px, py = self.pos().x(), self.pos().y()
        w, h = r.width(), r.height()
        MIN_W, MIN_H = 40, 40

        if corner == 'tl':
            new_w = (px + w) - (px + local.x())
            new_h = (py + h) - (py + local.y())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, new_h)
            self.setPos(px + w - new_w, py + h - new_h)
            self._rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'tr':
            new_w = max(MIN_W, local.x())
            new_h = (py + h) - (py + local.y())
            new_h = max(MIN_H, new_h)
            self.setPos(px, py + h - new_h)
            self._rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'bl':
            new_w = (px + w) - (px + local.x())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, local.y())
            self.setPos(px + w - new_w, py)
            self._rect = QRectF(0, 0, new_w, new_h)
        else:  # 'br'
            new_w = max(MIN_W, local.x())
            new_h = max(MIN_H, local.y())
            self._rect = QRectF(0, 0, new_w, new_h)

        self._update_handle_positions()

    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        if change == QGraphicsItem.ItemSelectedChange:
            self._set_handles_visible(bool(value))
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                try:
                    from core.connection import SmartConnection
                    for item in self.scene().items():
                        if isinstance(item, SmartConnection) and (item.source == self or item.target == self):
                            item.update_path()
                except:
                    pass
        return super().itemChange(change, value)



# --------------------------------------------------
# AV SLIDER
# --------------------------------------------------
class MediaAVSliderItem(MediaItem):
    CONTROLS_H = 90
    PLAYLIST_H = 60

    def __init__(self, sources: list[str], parent: QObject = None):
        super().__init__(parent)
        self._sources = list(sources)
        self._index = 0
        self._video_rect = QRectF(0, 0, 320, 180)
        self._rect = QRectF(0, 0, self._video_rect.width(), self._video_rect.height() + self.CONTROLS_H + self.PLAYLIST_H)

        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)

        self.handles = {
            'tl': Handle(self, 'tl'),
            'tr': Handle(self, 'tr'),
            'bl': Handle(self, 'bl'),
            'br': Handle(self, 'br'),
        }
        self._set_handles_visible(False)

        self._audio = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)
        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumSize(320, 180)
        self._video_widget.setStyleSheet("background-color: #000;")
        self._video_widget.show()

        ctrl = QWidget()
        ctrl.setAttribute(Qt.WA_TranslucentBackground)
        vlay = QVBoxLayout(ctrl)
        vlay.setContentsMargins(6, 6, 6, 6)
        vlay.setSpacing(4)
        
        # Controls usando QLabel clicável
        from PySide6.QtWidgets import QHBoxLayout
        controls_row = QWidget()
        controls_row.setAttribute(Qt.WA_TranslucentBackground)
        hlay = QHBoxLayout(controls_row)
        hlay.setContentsMargins(0, 0, 0, 0)
        
        prev = QLabel("◀")
        prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        prev.setFixedSize(30, 20)
        prev.setMouseTracking(True)
        
        play = QLabel("▶")
        play.setAlignment(Qt.AlignCenter)
        play.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        play.setFixedSize(30, 20)
        play.setMouseTracking(True)
        
        stop = QLabel("⏹")
        stop.setAlignment(Qt.AlignCenter)
        stop.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        stop.setFixedSize(30, 20)
        stop.setMouseTracking(True)
        
        nxt = QLabel("⏭")
        nxt.setAlignment(Qt.AlignCenter)
        nxt.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        nxt.setFixedSize(30, 20)
        nxt.setMouseTracking(True)
        
        self._label = QLabel("1/1")
        self._label.setAlignment(Qt.AlignCenter)
        
        # Conectar cliques
        prev.mousePressEvent = lambda e: self._prev()
        play.mousePressEvent = lambda e: self._player.play()
        stop.mousePressEvent = lambda e: self._player.stop()
        nxt.mousePressEvent = lambda e: self._next()
        
        hlay.addWidget(prev)
        hlay.addWidget(play)
        hlay.addWidget(stop)
        hlay.addWidget(nxt)
        hlay.addWidget(self._label)
        vlay.addWidget(controls_row)
        # Progresso e volume
        self._progress = QSlider(Qt.Horizontal)
        self._progress.setRange(0, 0)
        self._volume = QSlider(Qt.Horizontal)
        self._volume.setRange(0, 100)
        self._volume.setValue(50)
        vlay.addWidget(self._progress)
        vlay.addWidget(QLabel("Volume"))
        vlay.addWidget(self._volume)
        # Rótulos de tempo e mudo
        try:
            from PySide6.QtWidgets import QHBoxLayout, QCheckBox
            time_lay = QHBoxLayout()
            self._lab_cur = QLabel("00:00")
            self._lab_tot = QLabel("00:00")
            self._mute = QCheckBox("Mudo")
            time_lay.addWidget(self._lab_cur)
            time_lay.addStretch(1)
            time_lay.addWidget(self._lab_tot)
            time_lay.addStretch(1)
            time_lay.addWidget(self._mute)
            vlay.addLayout(time_lay)
        except Exception:
            pass
        
        # Playlist row - lista de vídeos
        playlist_row = QWidget()
        playlist_row.setAttribute(Qt.WA_TranslucentBackground)
        phlay = QHBoxLayout(playlist_row)
        phlay.setContentsMargins(0, 0, 0, 0)
        self._playlist_buttons = []
        for idx, src in enumerate(self._sources):
            btn = QLabel(str(idx + 1))
            btn.setAlignment(Qt.AlignCenter)
            btn.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
            btn.setFixedSize(30, 25)
            btn.setMouseTracking(True)
            btn.mousePressEvent = lambda e, i=idx: self._go_to_index(i)
            self._playlist_buttons.append(btn)
            phlay.addWidget(btn)
        phlay.addStretch()
        vlay.addWidget(playlist_row)

        container = QWidget()
        container.setMinimumSize(320, 250)
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)
        container_lay.addWidget(self._video_widget, 1)
        container_lay.addWidget(ctrl, 0)

        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(container)
        self._proxy.setAcceptHoverEvents(True)
        self._proxy.setFlag(QGraphicsProxyWidget.ItemSendsGeometryChanges, True)
        container.setFocusPolicy(Qt.NoFocus)
        self._update_proxy_geometry()
        self._update_handle_positions()

        self._player.setVideoOutput(self._video_widget)
        
        # Conectar sinais de estado para feedback
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.errorOccurred.connect(self._on_error_occurred)
        
        self._load_current()
        
        # Garantir que o vídeo widget está visível
        self._video_widget.show()
        
        # Tentar iniciar reprodução automaticamente após um pequeno atraso
        QTimer.singleShot(500, self._player.play)
        
        # Ligações de progresso/volume
        try:
            self._player.positionChanged.connect(lambda pos: self._progress.setValue(int(pos)))
            self._player.durationChanged.connect(lambda dur: self._progress.setRange(0, int(dur)))
            self._progress.sliderMoved.connect(self._player.setPosition)
            self._audio.setVolume(self._volume.value()/100.0)
            self._volume.valueChanged.connect(lambda v: self._audio.setVolume(v/100.0))
            # Tempo e mudo
            def _fmt(ms: int) -> str:
                s = max(0, int(ms//1000))
                m = s//60
                s = s%60
                return f"{m:02d}:{s:02d}"
            if hasattr(self, '_lab_cur'):
                self._player.positionChanged.connect(lambda pos: self._lab_cur.setText(_fmt(pos)))
            if hasattr(self, '_lab_tot'):
                self._player.durationChanged.connect(lambda dur: self._lab_tot.setText(_fmt(dur)))
            if hasattr(self, '_mute'):
                self._mute.toggled.connect(self._audio.setMuted)
        except Exception:
            pass

    def _on_playback_state_changed(self, state):
        """Callback quando o estado de reprodução muda"""
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._label.setText(f"▶ {self._index+1}/{len(self._sources)}")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._label.setText(f"⏸ {self._index+1}/{len(self._sources)}")
        else:
            self._label.setText(f"{self._index+1}/{len(self._sources)}")

    def _on_error_occurred(self):
        """Callback quando ocorre um erro"""
        from PySide6.QtMultimedia import QMediaPlayer
        error = self._player.error()
        if error != QMediaPlayer.Error.NoError:
            error_str = self._player.errorString()
            self._label.setText(f"Erro!")
            if hasattr(self, '_label'):
                self._label.setToolTip(error_str)

    def _load_current(self):
        if not self._sources:
            return
        try:
            from PySide6.QtCore import QUrl
            source_str = str(self._sources[self._index])
            if source_str.startswith('http://') or source_str.startswith('https://'):
                self._player.setSource(QUrl(source_str))
            else:
                self._player.setSource(QUrl.fromLocalFile(source_str))
            self._label.setText(f"{self._index+1}/{len(self._sources)}")
        except Exception:
            pass

    def _go_to_index(self, idx):
        if 0 <= idx < len(self._sources):
            self._index = idx
            self._load_current()
            self._player.play()
            self._update_playlist_buttons()

    def _update_playlist_buttons(self):
        if hasattr(self, '_playlist_buttons'):
            for idx, btn in enumerate(self._playlist_buttons):
                if idx == self._index:
                    btn.setStyleSheet("background-color: #0078d4; color: white;")
                else:
                    btn.setStyleSheet("")

    def _prev(self):
        if not self._sources:
            return
        self._index = (self._index - 1) % len(self._sources)
        self._load_current()
        self._player.play()
        self._update_playlist_buttons()

    def _next(self):
        if not self._sources:
            return
        self._index = (self._index + 1) % len(self._sources)
        self._load_current()
        self._player.play()
        self._update_playlist_buttons()

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        pass

    def _update_proxy_geometry(self):
        if hasattr(self, '_proxy') and self._proxy is not None:
            self._proxy.setPos(0, 0)
            self._proxy.widget().setFixedWidth(int(self._rect.width()))
            self._proxy.widget().setFixedHeight(int(self._rect.height()))

    def _update_handle_positions(self):
        r = self._video_rect
        w, h = r.width(), r.height()
        self.handles['tl'].setPos(0, 0)
        self.handles['tr'].setPos(w, 0)
        self.handles['bl'].setPos(0, h)
        self.handles['br'].setPos(w, h)
        self._update_proxy_geometry()

    def _set_handles_visible(self, visible: bool):
        for h in self.handles.values():
            h.setVisible(visible)

    def resize_from_corner(self, corner: str, scene_pos):
        self.prepareGeometryChange()
        local = self.mapFromScene(scene_pos)
        r = self._video_rect
        px, py = self.pos().x(), self.pos().y()
        w, h = r.width(), r.height()
        MIN_W, MIN_H = 160, 90

        if corner == 'tl':
            new_w = (px + w) - (px + local.x())
            new_h = (py + h) - (py + local.y())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, new_h)
            self.setPos(px + w - new_w, py + h - new_h)
            self._video_rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'tr':
            new_w = max(MIN_W, local.x())
            new_h = (py + h) - (py + local.y())
            new_h = max(MIN_H, new_h)
            self.setPos(px, py + h - new_h)
            self._video_rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'bl':
            new_w = (px + w) - (px + local.x())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, local.y())
            self.setPos(px + w - new_w, py)
            self._video_rect = QRectF(0, 0, new_w, new_h)
        else:
            new_w = max(MIN_W, local.x())
            new_h = max(MIN_H, local.y())
            self._video_rect = QRectF(0, 0, new_w, new_h)

        self._rect = QRectF(0, 0, self._video_rect.width(), self._video_rect.height() + self.CONTROLS_H + self.PLAYLIST_H)
        self._update_handle_positions()

    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        if change == QGraphicsItem.ItemSelectedChange:
            self._set_handles_visible(bool(value))
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                try:
                    from core.connection import SmartConnection
                    for item in self.scene().items():
                        if isinstance(item, SmartConnection) and (item.source == self or item.target == self):
                            item.update_path()
                except:
                    pass
        return super().itemChange(change, value)

class MediaAVItem(MediaItem):
    CONTROLS_H = 40

    def __init__(self, source: str, parent: QObject = None):
        super().__init__(parent)
        self.source = source
        self._video_rect = QRectF(0, 0, 360, 200)
        self._rect = QRectF(0, 0, self._video_rect.width(), self._video_rect.height() + self.CONTROLS_H)

        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)

        self.handles = {
            'tl': Handle(self, 'tl'),
            'tr': Handle(self, 'tr'),
            'bl': Handle(self, 'bl'),
            'br': Handle(self, 'br'),
        }
        self._set_handles_visible(False)

        # Player setup - apenas áudio
        self._audio = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)
        
        # Placeholder para vídeo
        self._video_placeholder = QLabel()
        self._video_placeholder.setAlignment(Qt.AlignCenter)
        self._video_placeholder.setStyleSheet("background-color: #222; color: #888; border: 2px solid #444; border-radius: 8px;")
        self._video_placeholder.setMinimumSize(320, 180)
        self._video_placeholder.setText("🎬 Vídeo\n(áudio disponível)")

        # Controls usando QLabel clicável
        from PySide6.QtWidgets import QHBoxLayout as HBoxLay
        ctrl = QWidget()
        ctrl.setAttribute(Qt.WA_TranslucentBackground)
        vlay = QVBoxLayout(ctrl)
        vlay.setContentsMargins(6, 6, 6, 6)
        vlay.setSpacing(4)
        
        controls_row = QWidget()
        controls_row.setAttribute(Qt.WA_TranslucentBackground)
        hlay = HBoxLay(controls_row)
        hlay.setContentsMargins(10, 0, 10, 0)
        
        prev = QLabel("◀")
        prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet("background-color: #ddd; padding: 4px; border-radius: 3px; margin: 2px;")
        prev.setFixedSize(35, 25)
        prev.setMouseTracking(True)
        
        play = QLabel("▶")
        play.setAlignment(Qt.AlignCenter)
        play.setStyleSheet("background-color: #ddd; padding: 4px; border-radius: 3px; margin: 2px;")
        play.setFixedSize(35, 25)
        play.setMouseTracking(True)
        
        stop = QLabel("⏹")
        stop.setAlignment(Qt.AlignCenter)
        stop.setStyleSheet("background-color: #ddd; padding: 4px; border-radius: 3px; margin: 2px;")
        stop.setFixedSize(35, 25)
        stop.setMouseTracking(True)
        
        # Conectar cliques
        play.mousePressEvent = lambda e: self._player.play()
        stop.mousePressEvent = lambda e: self._player.stop()
        
        hlay.addWidget(prev)
        hlay.addWidget(play)
        hlay.addWidget(stop)
        hlay.addStretch()
        vlay.addWidget(controls_row)
        # Progresso e volume
        self._progress = QSlider(Qt.Horizontal)
        self._progress.setRange(0, 0)
        self._volume = QSlider(Qt.Horizontal)
        self._volume.setRange(0, 100)
        self._volume.setValue(50)
        vlay.addWidget(self._progress)
        vlay.addWidget(QLabel("Volume"))
        vlay.addWidget(self._volume)

        # Proxy composto: vídeo acima, controles abaixo
        container = QWidget()
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)
        container_lay.addWidget(self._video_placeholder, 1)
        container_lay.addWidget(ctrl, 0)

        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(container)
        self._update_proxy_geometry()
        self._update_handle_positions()

        # Set media source
        try:
            from PySide6.QtCore import QUrl
            source_str = str(source)
            if source_str.startswith('http://') or source_str.startswith('https://'):
                self._player.setSource(QUrl(source_str))
            else:
                self._player.setSource(QUrl.fromLocalFile(source_str))
        except Exception:
            pass

        # Ligações de progresso/volume
        try:
            self._player.positionChanged.connect(lambda pos: self._progress.setValue(int(pos)))
            self._player.durationChanged.connect(lambda dur: self._progress.setRange(0, int(dur)))
            self._progress.sliderMoved.connect(self._player.setPosition)
            self._audio.setVolume(self._volume.value()/100.0)
            self._volume.valueChanged.connect(lambda v: self._audio.setVolume(v/100.0))
        except Exception:
            pass

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        # Nada a desenhar: o conteúdo é o proxy com widgets reais
        pass

    def _update_proxy_geometry(self):
        if hasattr(self, '_proxy') and self._proxy is not None:
            self._proxy.setPos(0, 0)
            self._proxy.widget().setFixedWidth(int(self._rect.width()))
            self._proxy.widget().setFixedHeight(int(self._rect.height()))

    def _update_handle_positions(self):
        r = self._video_rect
        w, h = r.width(), r.height()
        self.handles['tl'].setPos(0, 0)
        self.handles['tr'].setPos(w, 0)
        self.handles['bl'].setPos(0, h)
        self.handles['br'].setPos(w, h)
        self._update_proxy_geometry()

    def _set_handles_visible(self, visible: bool):
        for h in self.handles.values():
            h.setVisible(visible)

    def resize_from_corner(self, corner: str, scene_pos):
        self.prepareGeometryChange()
        local = self.mapFromScene(scene_pos)
        r = self._video_rect
        px, py = self.pos().x(), self.pos().y()
        w, h = r.width(), r.height()
        MIN_W, MIN_H = 160, 90

        if corner == 'tl':
            new_w = (px + w) - (px + local.x())
            new_h = (py + h) - (py + local.y())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, new_h)
            self.setPos(px + w - new_w, py + h - new_h)
            self._video_rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'tr':
            new_w = max(MIN_W, local.x())
            new_h = (py + h) - (py + local.y())
            new_h = max(MIN_H, new_h)
            self.setPos(px, py + h - new_h)
            self._video_rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'bl':
            new_w = (px + w) - (px + local.x())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, local.y())
            self.setPos(px + w - new_w, py)
            self._video_rect = QRectF(0, 0, new_w, new_h)
        else:
            new_w = max(MIN_W, local.x())
            new_h = max(MIN_H, local.y())
            self._video_rect = QRectF(0, 0, new_w, new_h)

        self._rect = QRectF(0, 0, self._video_rect.width(), self._video_rect.height() + self.CONTROLS_H)
        self._update_handle_positions()

    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        if change == QGraphicsItem.ItemSelectedChange:
            self._set_handles_visible(bool(value))
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                try:
                    from core.connection import SmartConnection
                    for item in self.scene().items():
                        if isinstance(item, SmartConnection) and (item.source == self or item.target == self):
                            item.update_path()
                except:
                    pass
        return super().itemChange(change, value)


class MediaSliderImageItem(MediaItem):
    CONTROLS_H = 60
    PLAYLIST_H = 80

    def __init__(self, images: list[QImage], sources: list[str] | None = None, parent: QObject = None):
        super().__init__(parent)
        self._entries = []  # cada entrada: {"pix": QPixmap, "movie": QMovie|None, "source": str}
        for idx, img in enumerate(images):
            pix = QPixmap.fromImage(img) if not img.isNull() else QPixmap()
            movie = None
            source = ""
            try:
                if sources and idx < len(sources):
                    source = sources[idx]
                    low = str(source).lower()
                    if low.endswith((".gif", ".webp")):
                        mv = QMovie(source)
                        if mv.isValid():
                            movie = mv
                            mv.frameChanged.connect(self.update)
                            mv.start()
                            if (not pix) or pix.isNull():
                                pix = mv.currentPixmap()
            except Exception:
                pass
            self._entries.append({"pix": pix, "movie": movie, "source": source})

        if not self._entries:
            dummy = QPixmap(40, 40)
            dummy.fill(Qt.lightGray)
            self._entries = [{"pix": dummy, "movie": None, "source": ""}]
        self._index = 0
        first = self._entries[0]["pix"]
        w = max(80, first.width() or 80)
        h = max(60, first.height() or 60)
        self._img_rect = QRectF(0, 0, w, h)
        self._rect = QRectF(0, 0, w, h + self.CONTROLS_H + self.PLAYLIST_H)

        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)

        self.handles = {
            'tl': Handle(self, 'tl'),
            'tr': Handle(self, 'tr'),
            'bl': Handle(self, 'bl'),
            'br': Handle(self, 'br'),
        }
        self._set_handles_visible(False)

        # Controles e proxy
        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.timeout.connect(self._next)
        self._controls_widget = self._build_controls()
        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(self._controls_widget)
        
        # Configurações para permitir cliques nos botões
        self._proxy.setFlag(QGraphicsProxyWidget.ItemIsFocusable, False)
        self._proxy.setAcceptHoverEvents(False)
        
        # Não instalar event filter - causa problemas
        # Deixe os botões funcionarem naturalmente
        
        self._update_proxy_geometry()
        self._update_handle_positions()

    def eventFilter(self, obj, event):
        # Force mouse release to prevent stuck buttons
        if event.type() == QEvent.MouseButtonRelease:
            for btn in self._controls_widget.findChildren(QPushButton):
                btn.releaseMouse()
        return super().eventFilter(obj, event)

    def _build_controls(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WA_TranslucentBackground)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        
        # Controls row
        controls_row = QWidget()
        controls_row.setAttribute(Qt.WA_TranslucentBackground)
        hlay = QHBoxLayout(controls_row)
        hlay.setContentsMargins(0, 0, 0, 0)
        
        # Usar QLabel clicável em vez de QPushButton
        prev = QLabel("◀")
        prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        prev.setFixedSize(30, 20)
        prev.setMouseTracking(True)
        
        play = QLabel("▶")
        play.setAlignment(Qt.AlignCenter)
        play.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        play.setFixedSize(30, 20)
        play.setMouseTracking(True)
        
        pause = QLabel("⏸")
        pause.setAlignment(Qt.AlignCenter)
        pause.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        pause.setFixedSize(30, 20)
        pause.setMouseTracking(True)
        
        nxt = QLabel("⏭")
        nxt.setAlignment(Qt.AlignCenter)
        nxt.setStyleSheet("background-color: #ddd; padding: 2px; border-radius: 3px;")
        nxt.setFixedSize(30, 20)
        nxt.setMouseTracking(True)
        
        # Label de posição - acima dos botões
        self._label = QLabel(f"{self._index+1}/{len(self._entries)}")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("font-weight: bold; color: #333;")
        
        # Conectar cliques
        prev.mousePressEvent = lambda e: self._prev()
        play.mousePressEvent = lambda e: self._play()
        pause.mousePressEvent = lambda e: self._pause()
        nxt.mousePressEvent = lambda e: self._next()
        
        # Layout dos controles
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(2)
        
        # Linha 1: botões de controle
        controls_hlay = QHBoxLayout()
        controls_hlay.setContentsMargins(0, 0, 0, 0)
        controls_hlay.addWidget(prev)
        controls_hlay.addWidget(play)
        controls_hlay.addWidget(pause)
        controls_hlay.addWidget(nxt)
        controls_hlay.addStretch()
        
        controls_layout.addWidget(self._label)
        controls_layout.addLayout(controls_hlay)
        
        lay.addLayout(controls_layout)
        
        # Playlist row - thumbnails
        playlist_row = QWidget()
        playlist_row.setAttribute(Qt.WA_TranslucentBackground)
        phlay = QHBoxLayout(playlist_row)
        phlay.setContentsMargins(0, 0, 0, 0)
        
        self._playlist_labels = []
        for idx, entry in enumerate(self._entries):
            thumb_label = QLabel()
            thumb_label.setFixedSize(40, 40)
            pix = entry["pix"]
            if not pix.isNull():
                thumb_label.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumb_label.setStyleSheet("border: 1px solid #ccc;")
            thumb_label.setMouseTracking(True)
            thumb_label.mousePressEvent = lambda e, i=idx: self._go_to_index(i)
            self._playlist_labels.append(thumb_label)
            phlay.addWidget(thumb_label)
        
        # Adicionar spacer
        phlay.addStretch()
        lay.addWidget(playlist_row)
        
        return w

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        entry = self._entries[self._index]
        pix = entry["pix"]
        movie = entry["movie"]
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        target = self._img_rect.toRect()
        if movie is not None:
            frame = movie.currentPixmap()
            if not frame.isNull():
                painter.drawPixmap(target, frame.scaled(target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif not pix.isNull():
            painter.drawPixmap(target, pix.scaled(target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _update_label(self):
        if hasattr(self, "_label") and self._label is not None:
            try:
                self._label.setText(f"{self._index+1}/{len(self._entries)}")
            except RuntimeError:
                pass
        if hasattr(self, "_playlist_labels") and self._playlist_labels:
            try:
                for idx, label in enumerate(self._playlist_labels):
                    if label is None:
                        continue
                    if idx == self._index:
                        label.setStyleSheet("border: 2px solid #0078d4;")
                    else:
                        label.setStyleSheet("border: 1px solid #ccc;")
            except RuntimeError:
                pass

    def _go_to_index(self, idx):
        if 0 <= idx < len(self._entries):
            self._index = idx
            self._update_label()
            self.update()

    def _prev(self):
        self._index = (self._index - 1) % len(self._entries)
        self._update_label()
        self.update()

    def _next(self):
        self._index = (self._index + 1) % len(self._entries)
        self._update_label()
        self.update()

    def _play(self):
        self._timer.start()

    def _pause(self):
        self._timer.stop()

    def _rebuild_playlist_widget(self):
        """Reconstrói as miniaturas da playlist"""
        if not hasattr(self, '_controls_widget') or self._controls_widget is None:
            return
        
        # Encontrar o layout da playlist
        playlist_layout = None
        for child in self._controls_widget.children():
            if isinstance(child, QVBoxLayout):
                for i in range(child.count()):
                    item = child.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        # Procurar pelo widget da playlist (geralmente o segundo widget)
                        for subchild in widget.children():
                            if isinstance(subchild, QHBoxLayout):
                                playlist_layout = subchild
                                break
                if playlist_layout:
                    break
        
        if not playlist_layout:
            return
        
        # Remover widgets antigos (manter o stretch)
        while playlist_layout.count() > 0:
            item = playlist_layout.itemAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                playlist_layout.takeAt(0)
        
        # Adicionar stretch primeiro
        playlist_layout.addStretch()
        
        # Criar novas miniaturas
        self._playlist_labels = []
        for idx, entry in enumerate(self._entries):
            thumb_label = QLabel()
            thumb_label.setFixedSize(40, 40)
            pix = entry["pix"]
            if not pix.isNull():
                thumb_label.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumb_label.setStyleSheet("border: 1px solid #ccc;")
            thumb_label.setMouseTracking(True)
            thumb_label.mousePressEvent = lambda e, i=idx: self._go_to_index(i)
            self._playlist_labels.append(thumb_label)
            
            # Inserir antes do stretch
            playlist_layout.insertWidget(playlist_layout.count() - 1, thumb_label)
        
        self._update_label()
        self.update()

    def _update_proxy_geometry(self):
        if hasattr(self, "_proxy") and self._proxy is not None:
            self._proxy.setPos(0, self._img_rect.height())
        if hasattr(self, "_controls_widget") and self._controls_widget is not None:
            self._controls_widget.setFixedHeight(self.CONTROLS_H + self.PLAYLIST_H)
            self._controls_widget.setFixedWidth(int(self._rect.width()))

    def _update_handle_positions(self):
        r = self._img_rect
        w, h = r.width(), r.height()
        self.handles['tl'].setPos(0, 0)
        self.handles['tr'].setPos(w, 0)
        self.handles['bl'].setPos(0, h)
        self.handles['br'].setPos(w, h)
        self._update_proxy_geometry()

    def _set_handles_visible(self, visible: bool):
        for h in self.handles.values():
            h.setVisible(visible)

    def resize_from_corner(self, corner: str, scene_pos):
        self.prepareGeometryChange()
        local = self.mapFromScene(scene_pos)
        r = self._img_rect
        px, py = self.pos().x(), self.pos().y()
        w, h = r.width(), r.height()
        MIN_W, MIN_H = 80, 60

        if corner == 'tl':
            new_w = (px + w) - (px + local.x())
            new_h = (py + h) - (py + local.y())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, new_h)
            self.setPos(px + w - new_w, py + h - new_h)
            self._img_rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'tr':
            new_w = max(MIN_W, local.x())
            new_h = (py + h) - (py + local.y())
            new_h = max(MIN_H, new_h)
            self.setPos(px, py + h - new_h)
            self._img_rect = QRectF(0, 0, new_w, new_h)
        elif corner == 'bl':
            new_w = (px + w) - (px + local.x())
            new_w = max(MIN_W, new_w)
            new_h = max(MIN_H, local.y())
            self.setPos(px + w - new_w, py)
            self._img_rect = QRectF(0, 0, new_w, new_h)
        else:  # 'br'
            new_w = max(MIN_W, local.x())
            new_h = max(MIN_H, local.y())
            self._img_rect = QRectF(0, 0, new_w, new_h)

        self._rect = QRectF(0, 0, self._img_rect.width(), self._img_rect.height() + self.CONTROLS_H + self.PLAYLIST_H)
        self._update_handle_positions()

    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        if change == QGraphicsItem.ItemSelectedChange:
            self._set_handles_visible(bool(value))
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                try:
                    from core.connection import SmartConnection
                    for item in self.scene().items():
                        if isinstance(item, SmartConnection) and (item.source == self or item.target == self):
                            item.update_path()
                except:
                    pass
        return super().itemChange(change, value)
