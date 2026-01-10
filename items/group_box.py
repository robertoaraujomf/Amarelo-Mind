from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt

class GroupBox(QGraphicsRectItem):
    """Retângulo amarelo tracejado para agrupar notas (Requisito 10)"""
    def __init__(self, rect):
        super().__init__(rect)
        # Configura a borda: Amarela, espessura 2, estilo Tracejado (DashLine)
        pen = QPen(QColor("#f2f71d"), 2, Qt.DashLine)
        self.setPen(pen)
        
        # Fundo amarelo bem clarinho e semi-transparente (Alpha 30)
        self.setBrush(QColor(242, 247, 29, 30)) 
        
        # Garante que o grupo fique atrás dos nós
        self.setZValue(-10) 
        
        # Permite que o grupo seja movido e selecionado
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)

    def paint(self, painter, option, widget):
        # Remove a borda de seleção padrão do Qt para não ficar feio
        option.state &= ~Qt.Style_Selected
        super().paint(painter, option, widget)