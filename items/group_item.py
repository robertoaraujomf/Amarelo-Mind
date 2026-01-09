from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QBrush

class MindMapGroup(QGraphicsRectItem):
    """Moldura de agrupamento com cantos arredondados (Botão 10)"""
    def __init__(self, items):
        super().__init__()
        self.child_items = items
        self.setZValue(-2) # Atrás de tudo
        
        # Estilo: Borda amarela pontilhada, fundo levemente escurecido
        self.setPen(QPen(QColor("#c3c910"), 2, Qt.DashLine))
        self.setBrush(QBrush(QColor(195, 201, 16, 20))) # Amarelo com transparência
        
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.update_boundary()

    def update_boundary(self):
        """Calcula o retângulo que envolve todos os filhos + margem"""
        if not self.child_items:
            return
            
        rect = self.child_items[0].sceneBoundingRect()
        for item in self.child_items[1:]:
            rect = rect.united(item.sceneBoundingRect())
            
        # Adiciona uma margem de 15px ao redor
        self.setRect(rect.adjusted(-15, -15, 15, 15))

    def paint(self, painter, option, widget):
        # Sobrescreve para desenhar cantos arredondados
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), 15, 15)