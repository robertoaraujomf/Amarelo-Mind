from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QBrush, QPainter
from PySide6.QtCore import Qt, QRectF

class GroupNode(QGraphicsRectItem):
    """Objeto que envolve outros nós (Requisito 10)"""
    def __init__(self, items_to_group):
        super().__init__()
        self.child_items = items_to_group
        
        # Estética: Retângulo Arredondado, sem preenchimento, borda tracejada
        self.setPen(QPen(QColor("#f2f71d"), 2, Qt.DashLine))
        self.setBrush(QColor(242, 247, 29, 20)) # Amarelo bem transparente
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Define que este grupo deve ser tratado como unidade (Observação 3)
        self.is_unit = True 
        
        self.calculate_bounds()

    def calculate_bounds(self):
        """Calcula o retângulo que engloba todos os itens selecionados"""
        if not self.child_items: return
        
        rect = self.child_items[0].sceneBoundingRect()
        for item in self.child_items[1:]:
            rect = rect.united(item.sceneBoundingRect())
        
        # Adiciona uma margem extra para o retângulo de grupo
        self.setRect(rect.adjusted(-15, -15, 15, 15))

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        # Requisito 10: Arredondado nas pontas
        painter.drawRoundedRect(r, 15, 15)

    def itemChange(self, change, value):
        # Quando o grupo move, todos os filhos movem juntos
        if change == QGraphicsItem.ItemPositionHasChanged:
            delta = value - self.pos()
            for item in self.child_items:
                item.moveBy(delta.x(), delta.y())
        return super().itemChange(change, value)