from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QCursor

class Handle(QGraphicsRectItem):
    """Handles de seleção e redimensionamento (Amarelo Mind Design)"""
    def __init__(self, parent, position_name):
        super().__init__(-4, -4, 8, 8, parent)
        self.parent_node = parent
        self.pos_name = position_name
        self.setBrush(QColor("#f2f71d"))
        self.setPen(QPen(QColor("#1a1a1a"), 1))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setZValue(100)
        
        # Define cursores específicos para cada posição
        cursors = {
            'h1': Qt.SizeFDiagCursor, 'h3': Qt.SizeBDiagCursor,
            'h6': Qt.SizeBDiagCursor, 'h8': Qt.SizeFDiagCursor,
            'h2': Qt.SizeVerCursor, 'h7': Qt.SizeVerCursor,
            'h4': Qt.SizeHorCursor, 'h5': Qt.SizeHorCursor
        }
        self.setCursor(cursors.get(position_name, Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        new_pos = self.mapToParent(event.pos())
        is_proportional = self.pos_name in ['h1', 'h3', 'h6', 'h8']
        self.parent_node.resize_logic(self.pos_name, new_pos, is_proportional)

class MindMapNode(QGraphicsRectItem):
    def __init__(self, x, y):
        super().__init__(0, 0, 150, 80)
        self.setPos(x, y)
        
        # 1. Texto Interno (Observação 2: Justaposto e respeitando o perímetro)
        self.text_item = QGraphicsTextItem("Novo Objeto", self)
        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # 2. Inicialização dos 8 Handles
        self.handles = {p: Handle(self, p) for p in ['h1','h2','h3','h4','h5','h6','h7','h8']}
        self.update_handle_positions()
        self.set_handles_visible(False)

    def mouseDoubleClickEvent(self, event):
        """Habilita edição de texto no double-click"""
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setFocus()
        super().mouseDoubleClickEvent(event)

    def update_handle_positions(self):
        """Atualiza a posição dos handles baseada no rect atual"""
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
        """Mantém o texto centralizado e verifica estouro de margem"""
        r = self.rect()
        tr = self.text_item.boundingRect()
        # Ajusta posição do texto
        self.text_item.setPos(r.center().x() - tr.width()/2, 
                             r.center().y() - tr.height()/2)
        
        # Bloqueio de Redimensionamento Automático (Tamanho Mínimo)
        # Se o texto for maior que o nó, o nó deve crescer.
        if tr.width() + 20 > r.width() or tr.height() + 20 > r.height():
            new_w = max(r.width(), tr.width() + 20)
            new_h = max(r.height(), tr.height() + 20)
            self.setRect(0, 0, new_w, new_h)
            self.update_handle_positions()

    def resize_logic(self, name, pos, proportional):
        """Lógica de redimensionamento proporcional vs livre"""
        r = self.rect()
        old_ratio = r.width() / r.height()
        
        # Cálculo básico de nova dimensão
        if name == 'h8': 
            r.setBottomRight(pos)
        elif name == 'h5': 
            r.setRight(pos.x())
        elif name == 'h7': 
            r.setBottom(pos.y())
        elif name == 'h1': 
            r.setTopLeft(pos)
        # ... outras posições seguem lógica similar ...

        # Aplicação da Proporcionalidade (h1, h3, h6, h8)
        if proportional:
            new_h = r.width() / old_ratio
            r.setHeight(new_h)

        # Bloqueio de tamanho mínimo baseado no conteúdo visível
        tr = self.text_item.boundingRect()
        min_w, min_h = tr.width() + 10, tr.height() + 10
        
        if r.width() >= min_w and r.height() >= min_h:
            self.setRect(r.normalized())
            self.update_handle_positions()

    def set_handles_visible(self, visible):
        for h in self.handles.values(): h.setVisible(visible)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.set_handles_visible(bool(value))
            if not bool(value):
                self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                from core.connection import SmartConnection
                for item in self.scene().items():
                    if isinstance(item, SmartConnection) and (item.source == self or item.target == self):
                        item.update_path()
        return super().itemChange(change, value)