from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainter

class SmartConnection(QGraphicsPathItem):
    """Conexão curva ou reta entre objetos"""
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        # Azul conforme solicitado para o ícone de conexão
        self.setPen(QPen(QColor("#0078d4"), 3, Qt.SolidLine, Qt.RoundCap))
        self.setZValue(-1) # Garante que a linha fique por baixo dos nós
        self.update_path()

    def update_path(self):
        if not self.source.scene() or not self.target.scene():
            return

        sc = self.source.sceneBoundingRect().center()
        tc = self.target.sceneBoundingRect().center()
        dx = tc.x() - sc.x()
        dy = tc.y() - sc.y()
        dist = max((dx**2 + dy**2)**0.5, 1)

        path = QPainterPath()
        path.moveTo(sc)

        # Sempre curvas: Bezier cúbico com controle perpendicular ao segmento
        k = min(0.35 * dist, 80)
        nx, ny = -dy / dist, dx / dist
        c1 = QPointF(sc.x() + dx * 0.5 + nx * k, sc.y() + dy * 0.5 + ny * k)
        c2 = QPointF(sc.x() + dx * 0.5 - nx * k, sc.y() + dy * 0.5 - ny * k)
        path.cubicTo(c1, c2, tc)

        self.setPath(path)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        self.update_path() # Força o ajuste da linha durante o movimento
        super().paint(painter, option, widget)