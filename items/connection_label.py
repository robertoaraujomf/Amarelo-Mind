from PySide6.QtWidgets import QGraphicsTextItem
from PySide6.QtGui import QColor, QFont

class ConnectionLabel(QGraphicsTextItem):
    """Texto que fica preso no meio de uma linha de conexão (Requisito 13)"""
    def __init__(self, text="relação", parent_connection=None):
        super().__init__(text, parent_connection)
        self.setDefaultTextColor(QColor("#555555"))
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.parent_conn = parent_connection
        self.setZValue(10)

    def update_position(self):
        """Calcula o ponto médio da linha para posicionar o texto"""
        line = self.parent_conn.line()
        mid_point = line.pointAt(0.5)
        self.setPos(mid_point.x() - self.boundingRect().width()/2, 
                    mid_point.y() - self.boundingRect().height()/2)