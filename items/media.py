from PySide6.QtWidgets import QGraphicsObject, QWidget, QHBoxLayout, QPushButton, QLabel, QGraphicsProxyWidget, QVBoxLayout, QMenu, QAction, QFileDialog, QSlider
from PySide6.QtCore import QObject
from PySide6.QtGui import QPixmap, QImage, QPainter
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
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        menu = QMenu()
        act_add = QAction("Adicionar vídeos/áudios…", menu)
        act_remove_current = QAction("Remover faixa atual", menu)
        act_to_single = QAction("Converter para AV único", menu)
        menu.addAction(act_add)
        menu.addAction(act_remove_current)
        menu.addAction(act_to_single)
        chosen = menu.exec(event.screenPos().toPoint())
        if not chosen:
            return
        if chosen == act_add:
            filters = "Áudio/Vídeo (*.mp3 *.wav *.ogg *.mp4 *.avi *.mkv *.mov)"
            paths, _ = QFileDialog.getOpenFileNames(None, "Selecionar AV", "", filters)
            if not paths:
                return
            new_sources = list(self._sources) + paths
            slider = MediaAVSliderItem(new_sources)
            slider.setPos(self.pos())
            self._replace_self(slider, "Adicionar faixas ao slider AV")
        elif chosen == act_remove_current:
            if len(self._sources) <= 1:
                return
            new_sources = list(self._sources)
            del new_sources[self._index]
            slider = MediaAVSliderItem(new_sources)
            slider.setPos(self.pos())
            self._replace_self(slider, "Remover faixa do slider AV")
        elif chosen == act_to_single:
            if not self._sources:
                return
            src = self._sources[self._index]
            single = MediaAVItem(src)
            single.setPos(self.pos())
            self._replace_self(single, "Converter slider AV para AV único")

    def contextMenuEvent(self, event):
        menu = QMenu()
        act_add = QAction("Adicionar imagens…", menu)
        act_remove_current = QAction("Remover imagem atual", menu)
        act_to_single = QAction("Converter para imagem única", menu)
        menu.addAction(act_add)
        menu.addAction(act_remove_current)
        menu.addAction(act_to_single)
        chosen = menu.exec(event.screenPos().toPoint())
        if not chosen:
            return
        if chosen == act_add:
            filters = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            paths, _ = QFileDialog.getOpenFileNames(None, "Selecionar imagens", "", filters)
            if not paths:
                return
            all_imgs = [e["pix"].toImage() for e in self._entries]
            for p in paths:
                img = QImage(p)
                if not img.isNull():
                    all_imgs.append(img)
            slider = MediaSliderImageItem(all_imgs, None)
            slider.setPos(self.pos())
            self._replace_self(slider, "Adicionar imagens ao slider")
        elif chosen == act_remove_current:
            if len(self._entries) <= 1:
                return
            all_imgs = [e["pix"].toImage() for e in self._entries]
            del all_imgs[self._index]
            slider = MediaSliderImageItem(all_imgs, None)
            slider.setPos(self.pos())
            self._replace_self(slider, "Remover imagem do slider")
        elif chosen == act_to_single:
            entry = self._entries[self._index]
            img = entry["pix"].toImage() if isinstance(entry["pix"], QPixmap) else QImage()
            single = MediaImageItem(img)
            single.setPos(self.pos())
            self._replace_self(single, "Converter slider para imagem única")

    def contextMenuEvent(self, event):
        menu = QMenu()
        act_to_slider = QAction("Transformar em slider AV…", menu)
        act_add = QAction("Adicionar vídeos/áudios…", menu)
        menu.addAction(act_to_slider)
        menu.addAction(act_add)
        chosen = menu.exec(event.screenPos().toPoint())
        if not chosen:
            return
        filters = "Áudio/Vídeo (*.mp3 *.wav *.ogg *.mp4 *.avi *.mkv *.mov)"
        paths, _ = QFileDialog.getOpenFileNames(None, "Selecionar AV", "", filters)
        if not paths:
            return
        sources = [self.source] + paths
        slider = MediaAVSliderItem(sources)
        slider.setPos(self.pos())
        self._replace_self(slider, "Transformar AV em slider")

    def contextMenuEvent(self, event):
        menu = QMenu()
        act_to_slider = QAction("Transformar em slider…", menu)
        act_add_more = QAction("Adicionar imagens…", menu)
        menu.addAction(act_to_slider)
        menu.addAction(act_add_more)
        chosen = menu.exec(event.screenPos().toPoint())
        if not chosen:
            return
        filters = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        paths, _ = QFileDialog.getOpenFileNames(None, "Selecionar imagens", "", filters)
        if not paths:
            return
        imgs = []
        for p in paths:
            img = QImage(p)
            if not img.isNull():
                imgs.append((img, p))
        if not imgs:
            return
        all_images = [self._pix.toImage()] + [im for im, _ in imgs]
        sources = [self.source] + [s for _, s in imgs]
        slider = MediaSliderImageItem(all_images, sources)
        slider.setPos(self.pos())
        self._replace_self(slider, "Transformar imagem em slider")

# --------------------------------------------------
# AV SLIDER
# --------------------------------------------------
class MediaAVSliderItem(MediaItem):
    CONTROLS_H = 40

    def __init__(self, sources: list[str], parent: QObject = None):
        super().__init__(parent)
        self._sources = list(sources)
        self._index = 0
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

        self._audio = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)
        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumHeight(100)

        ctrl = QWidget()
        vlay = QVBoxLayout(ctrl)
        vlay.setContentsMargins(6, 6, 6, 6)
        vlay.setSpacing(4)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        btn_prev = QPushButton('◀')
        btn_play = QPushButton('▶')
        btn_pause = QPushButton('⏸')
        btn_stop = QPushButton('⏹')
        btn_next = QPushButton('▶')
        self._label = QLabel("1/1")
        for b in (btn_prev, btn_play, btn_pause, btn_stop, btn_next):
            b.setFixedHeight(self.CONTROLS_H - 12)
        hlay.addWidget(btn_prev)
        hlay.addWidget(btn_play)
        hlay.addWidget(btn_pause)
        hlay.addWidget(btn_stop)
        hlay.addWidget(btn_next)
        hlay.addWidget(self._label)
        vlay.addLayout(hlay)
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

        container = QWidget()
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)
        container_lay.addWidget(self._video_widget, 1)
        container_lay.addWidget(ctrl, 0)

        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(container)
        self._update_proxy_geometry()
        self._update_handle_positions()

        btn_play.clicked.connect(self._player.play)
        btn_pause.clicked.connect(self._player.pause)
        btn_stop.clicked.connect(self._player.stop)
        btn_prev.clicked.connect(self._prev)
        btn_next.clicked.connect(self._next)
        self._player.setVideoOutput(self._video_widget)
        self._load_current()
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

    def _load_current(self):
        if not self._sources:
            return
        try:
            from PySide6.QtCore import QUrl
            self._player.setSource(QUrl.fromLocalFile(self._sources[self._index]))
            self._label.setText(f"{self._index+1}/{len(self._sources)}")
        except Exception:
            pass

    def _prev(self):
        if not self._sources:
            return
        self._index = (self._index - 1) % len(self._sources)
        self._load_current()
        self._player.play()

    def _next(self):
        if not self._sources:
            return
        self._index = (self._index + 1) % len(self._sources)
        self._load_current()
        self._player.play()

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

        self._rect = QRectF(0, 0, self._video_rect.width(), self._video_rect.height() + self.CONTROLS_H)
        self._update_handle_positions()

    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        if change == QGraphicsItem.ItemSelectedChange:
            self._set_handles_visible(bool(value))
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

        # Player setup
        self._audio = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)

        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumHeight(100)

        # Controls
        ctrl = QWidget()
        vlay = QVBoxLayout(ctrl)
        vlay.setContentsMargins(6, 6, 6, 6)
        vlay.setSpacing(4)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        btn_prev = QPushButton('◀')
        btn_play = QPushButton('▶')
        btn_pause = QPushButton('⏸')
        btn_stop = QPushButton('⏹')
        btn_next = QPushButton('▶')
        for b in (btn_prev, btn_play, btn_pause, btn_stop, btn_next):
            b.setFixedHeight(self.CONTROLS_H - 12)
        hlay.addWidget(btn_prev)
        hlay.addWidget(btn_play)
        hlay.addWidget(btn_pause)
        hlay.addWidget(btn_stop)
        hlay.addWidget(btn_next)
        vlay.addLayout(hlay)
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
        container_lay.addWidget(self._video_widget, 1)
        container_lay.addWidget(ctrl, 0)

        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(container)
        self._update_proxy_geometry()
        self._update_handle_positions()

        # Wire controls
        btn_play.clicked.connect(self._player.play)
        btn_pause.clicked.connect(self._player.pause)
        btn_stop.clicked.connect(self._player.stop)
        # prev/next placeholders (playlist futura)
        btn_prev.setEnabled(False)
        btn_next.setEnabled(False)

        # Set media source
        try:
            from PySide6.QtCore import QUrl
            self._player.setVideoOutput(self._video_widget)
            self._player.setSource(QUrl.fromLocalFile(source))
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
        return super().itemChange(change, value)


class MediaSliderImageItem(MediaItem):
    CONTROLS_H = 36

    def __init__(self, images: list[QImage], sources: list[str] | None = None, parent: QObject = None):
        super().__init__(parent)
        self._entries = []  # cada entrada: {"pix": QPixmap, "movie": QMovie|None}
        for idx, img in enumerate(images):
            pix = QPixmap.fromImage(img) if not img.isNull() else QPixmap()
            movie = None
            try:
                if sources and idx < len(sources):
                    low = str(sources[idx]).lower()
                    if low.endswith((".gif", ".webp")):
                        mv = QMovie(sources[idx])
                        if mv.isValid():
                            movie = mv
                            mv.frameChanged.connect(self.update)
                            mv.start()
                            if (not pix) or pix.isNull():
                                pix = mv.currentPixmap()
            except Exception:
                pass
            self._entries.append({"pix": pix, "movie": movie})

        if not self._entries:
            dummy = QPixmap(40, 40)
            dummy.fill(Qt.lightGray)
            self._entries = [{"pix": dummy, "movie": None}]
        self._index = 0
        first = self._entries[0]["pix"]
        w = max(80, first.width() or 80)
        h = max(60, first.height() or 60)
        self._img_rect = QRectF(0, 0, w, h)
        self._rect = QRectF(0, 0, w, h + self.CONTROLS_H)

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
        self._update_proxy_geometry()
        self._update_handle_positions()

    def _build_controls(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        prev = QPushButton("◀")
        play = QPushButton("▶")
        pause = QPushButton("⏸")
        nxt = QPushButton("▶")
        self._label = QLabel(f"{self._index+1}/{len(self._entries)}")
        for btn in (prev, play, pause, nxt):
            btn.setFixedHeight(self.CONTROLS_H - 10)
        prev.clicked.connect(self._prev)
        play.clicked.connect(self._play)
        pause.clicked.connect(self._pause)
        nxt.clicked.connect(self._next)
        lay.addWidget(prev)
        lay.addWidget(play)
        lay.addWidget(pause)
        lay.addWidget(nxt)
        lay.addWidget(self._label)
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
        if hasattr(self, "_label"):
            self._label.setText(f"{self._index+1}/{len(self._entries)}")

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

    def _update_proxy_geometry(self):
        if hasattr(self, "_proxy") and self._proxy is not None:
            self._proxy.setPos(0, self._img_rect.height())
        if hasattr(self, "_controls_widget") and self._controls_widget is not None:
            self._controls_widget.setFixedHeight(self.CONTROLS_H)
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

        self._rect = QRectF(0, 0, self._img_rect.width(), self._img_rect.height() + self.CONTROLS_H)
        self._update_handle_positions()

    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        if change == QGraphicsItem.ItemSelectedChange:
            self._set_handles_visible(bool(value))
        return super().itemChange(change, value)
