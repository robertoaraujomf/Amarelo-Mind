from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor

class Handle(QGraphicsRectItem):
    def __init__(self, parent, position_name):
        super().__init__(-5, -5, 10, 10, parent)
        self.parent_node = parent
        self.pos_name = position_name
        self.setBrush(Qt.white)
        self.setPen(QPen(QColor("#2b2b2b"), 1))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setZValue(10) # Garante que fiquem acima de tudo no nó

    def mouseMoveEvent(self, event):
        new_pos = self.mapToParent(event.pos())
        self.parent_node.resize_logic(self.pos_name, new_pos)

class MindMapNode(QGraphicsRectItem):
    def __init__(self, x, y):
        super().__init__(0, 0, 150, 80)
        self.setPos(x, y)
        self.min_width, self.min_height = 100, 50
        
        # Texto interno
        self.text_item = QGraphicsTextItem("", self)
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                     QGraphicsItem.ItemIsSelectable | 
                     QGraphicsItem.ItemSendsGeometryChanges)
        
        # Inicializa handles h1 (top-left) até h8 (bottom-right)
        self.handles = {p: Handle(self, p) for p in ['h1','h2','h3','h4','h5','h6','h7','h8']}
        self.update_handle_positions()
        self.set_handles_visible(False)

    def update_handle_positions(self):
        r = self.rect()
        self.handles['h1'].setPos(r.topLeft())
        self.handles['h2'].setPos(r.center().x(), r.top())
        self.handles['h3'].setPos(r.topRight())
        self.handles['h4'].setPos(r.left(), r.center().y())
        self.handles['h5'].setPos(r.right(), r.center().y())
        self.handles['h6'].setPos(r.bottomLeft())
        self.handles['h7'].setPos(r.center().x(), r.bottom())
        self.handles['h8'].setPos(r.bottomRight())
        self.center_text()

    def center_text(self):
        """Centraliza o texto dentro do retângulo"""
        r = self.rect()
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(r.center().x() - text_rect.width()/2, 
                             r.center().y() - text_rect.height()/2)

    def resize_logic(self, name, pos):
        r = self.rect()
        p = self.pos()
        
        # Redimensionamento (ajusta o Rect e a Pos para manter o nó no lugar)
        if name == 'h8': # Bottom-Right
            r.setBottomRight(pos)
        elif name == 'h1': # Top-Left (Move o nó e encolhe o rect)
            diff = pos - r.topLeft()
            r.setTopLeft(pos)
            self.setPos(p + diff)
        elif name == 'h5': # Right
            r.setRight(pos.x())
        elif name == 'h7': # Bottom
            r.setBottom(pos.y())
        elif name == 'h4': # Left
            diff_x = pos.x() - r.left()
            r.setLeft(pos.x())
            self.setX(p.x() + diff_x)
        elif name == 'h2': # Top
            diff_y = pos.y() - r.top()
            r.setTop(pos.y())
            self.setY(p.y() + diff_y)

        # Aplica se respeitar o tamanho mínimo
        if r.width() >= self.min_width and r.height() >= self.min_height:
            # Normaliza o rect para (0,0, W, H) para evitar problemas de coordenadas locais
            new_rect = QRectF(0, 0, r.width(), r.height())
            self.setRect(new_rect)
            self.update_handle_positions()

    def set_handles_visible(self, visible):
        for h in self.handles.values(): h.setVisible(visible)

    def itemChange(self, change, value):
        # 1. Mostrar/Esconder Handles ao selecionar
        if change == QGraphicsItem.ItemSelectedChange:
            self.set_handles_visible(bool(value))
        
        # 2. Notificar Conexões para atualizar em tempo real
        if change == QGraphicsItem.ItemPositionHasChanged or change == QGraphicsItem.ItemRotationHasChanged:
            if self.scene():
                # Import dinâmico para evitar circular import
                from core.connection import SmartConnection
                for item in self.scene().items():
                    if isinstance(item, SmartConnection):
                        if item.source == self or item.target == self:
                            item.update_path()
                            
        return super().itemChange(change, value)