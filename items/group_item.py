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
        
        # Define posição e tamanho do grupo
        self.setPos(rect.topLeft())
        # Adiciona uma margem extra para o retângulo de grupo
        self.setRect(0, 0, rect.width() + 30, rect.height() + 30)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        # Requisito 10: Arredondado nas pontas
        painter.drawRoundedRect(r, 15, 15)

    def _update_children_connections(self):
        """Atualiza conexões de todos os filhos e do próprio grupo onde são destinos."""
        if not self.scene():
            return
        try:
            from core.connection import SmartConnection
            items_to_update = set(self.child_items)
            items_to_update.add(self)
            for conn in self.scene().items():
                if isinstance(conn, SmartConnection):
                    if conn.target in items_to_update:
                        conn.prepareGeometryChange()
                        conn.update_path()
        except:
            pass

    def itemChange(self, change, value):
        # Quando o grupo move, todos os filhos movem juntos
        if change == QGraphicsItem.ItemPositionChange:
            old_pos = self.pos()
            new_pos = value
            delta = new_pos - old_pos
            for item in self.child_items:
                if item.scene():
                    item.setPos(item.pos() + delta)
            return new_pos
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Recalcula bounds quando filhos se movem
            self.calculate_bounds()
            # Atualizar conexões dos filhos E do grupo onde são destinos
            self._update_children_connections()
        return super().itemChange(change, value)