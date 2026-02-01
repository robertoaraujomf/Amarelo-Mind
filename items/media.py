from PySide6.QtWidgets import QGraphicsObject, QWidget, QHBoxLayout, QPushButton, QLabel, QGraphicsProxyWidget
from PySide6.QtCore import QObject
from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtCore import QRectF, Qt, QTimer
from .shapes import Handle

class MediaItem(QGraphicsObject):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def paint(self, painter, option, widget=None):
        pass


class MediaImageItem(MediaItem):
    def __init__(self, image: QImage, source: str = "", parent: QObject = None):
        super().__init__(parent)
        self._pix = QPixmap.fromImage(image)
        w = max(40, self._pix.width())
        h = max(40, self._pix.height())
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
        if not self._pix.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.drawPixmap(self._rect.toRect(), self._pix.scaled(
                int(self._rect.width()), int(self._rect.height()),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
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


class MediaSliderImageItem(MediaItem):
    CONTROLS_H = 36

    def __init__(self, images: list[QImage], sources: list[str] | None = None, parent: QObject = None):
        super().__init__(parent)
        self._pixmaps = [QPixmap.fromImage(img) for img in images if not img.isNull()]
        if not self._pixmaps:
            self._pixmaps = [QPixmap(40, 40)]
            self._pixmaps[0].fill(Qt.lightGray)
        self._index = 0
        w = max(80, self._pixmaps[0].width())
        h = max(60, self._pixmaps[0].height())
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
        self._update_handle_positions()
        self._set_handles_visible(False)

        # Controles
        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.timeout.connect(self._next)
        self._controls_widget = self._build_controls()
        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(self._controls_widget)
        self._update_proxy_geometry()

    def _build_controls(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        prev = QPushButton("◀")
        play = QPushButton("▶")
        pause = QPushButton("⏸")
        nxt = QPushButton("▶")
        self._label = QLabel(f"{self._index+1}/{len(self._pixmaps)}")
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
        pix = self._pixmaps[self._index]
        if not pix.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            target = self._img_rect.toRect()
            painter.drawPixmap(target, pix.scaled(target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _update_label(self):
        if hasattr(self, "_label"):
            self._label.setText(f"{self._index+1}/{len(self._pixmaps)}")

    def _prev(self):
        self._index = (self._index - 1) % len(self._pixmaps)
        self._update_label()
        self.update()

    def _next(self):
        self._index = (self._index + 1) % len(self._pixmaps)
        self._update_label()
        self.update()

    def _play(self):
        self._timer.start()

    def _pause(self):
        self._timer.stop()

    def _update_proxy_geometry(self):
        self._proxy.setPos(0, self._img_rect.height())
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
