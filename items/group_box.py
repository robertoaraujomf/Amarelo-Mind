from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt

class GroupBox(QGraphicsRectItem):
    """Retângulo amarelo tracejado para agrupar notas (Requisito 10)"""
    def __init__(self, rect):
        super().__init__(rect)
        # Borda amarela tracejada
        pen = QPen(QColor("#f2f71d"), 2, Qt.DashLine)
        self.setPen(pen)
        # Fundo semi-transparente
        self.setBrush(QColor(242, 247, 29, 30)) 
        self.setZValue(-10) # Fica atrás dos nós
        self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable)