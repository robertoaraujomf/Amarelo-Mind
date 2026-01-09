from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QColor, QPainter
from PySide6.QtCore import Qt, QPointF

class SmartConnection(QGraphicsPathItem):
    def __init__(self, source_node, target_node):
        super().__init__()
        self.source = source_node
        self.target = target_node
        
        # Estilo da linha: Grafite suave
        self.setPen(QPen(QColor("#444444"), 2, Qt.SolidLine, Qt.RoundCap))
        self.setZValue(-1) # Fica atrás dos nós
        
        self.update_path()

    def update_path(self):
        """Calcula a curva de Bézier entre o centro dos dois nós"""
        path = QPainterPath()
        
        # Pontos centrais dos nós
        p1 = self.source.sceneBoundingRect().center()
        p2 = self.target.sceneBoundingRect().center()
        
        path.moveTo(p1)
        
        # Criamos pontos de controle para uma curva suave (S-shape)
        # O desvio horizontal cria um efeito orgânico de mapa mental
        dx = p2.x() - p1.x()
        ctrl1 = QPointF(p1.x() + dx / 2, p1.y())
        ctrl2 = QPointF(p1.x() + dx / 2, p2.y())
        
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)

    def paint(self, painter, option, widget):
        """Garante que a linha seja desenhada com suavização"""
        painter.setRenderHint(QPainter.Antialiasing)
        super().paint(painter, option, widget)