from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QApplication, QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QLinearGradient, QCursor

class Handle(QGraphicsRectItem):
    """Handles de seleção e redimensionamento nos vértices"""
    def __init__(self, parent, position_name):
        super().__init__(-4, -4, 8, 8, parent)
        self.parent_node = parent
        self.pos_name = position_name
        self.setBrush(QColor("#f2f71d"))
        self.setPen(QPen(QColor("#1a1a1a"), 1))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setZValue(100)
        
        cursors = {
            'h1': Qt.SizeFDiagCursor, 'h3': Qt.SizeBDiagCursor,
            'h6': Qt.SizeBDiagCursor, 'h8': Qt.SizeFDiagCursor,
            'h2': Qt.SizeVerCursor,   'h7': Qt.SizeVerCursor,
            'h4': Qt.SizeHorCursor,   'h5': Qt.SizeHorCursor
        }
        self.setCursor(cursors.get(position_name, Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        self.parent_node.resize_logic(self.pos_name, event.scenePos())

class StyledNode(QGraphicsRectItem):
    """Objeto Nó com redimensionamento, sem borda, com sombra lateral padrão"""
    def __init__(self, x, y, text="", brush=None, shadow=None):
        super().__init__(0, 0, 160, 60)
        self.setPos(x, y)
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                      QGraphicsRectItem.ItemIsSelectable | 
                      QGraphicsRectItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemClipsChildrenToShape)
        
        # Sem borda (borderless) conforme especificação
        self.setPen(QPen(Qt.NoPen))
        
        # Lógica de Cor: Se não houver brush, aplica o degradê amarelo padrão
        if brush:
            self.setBrush(brush)
        else:
            grad = QLinearGradient(0, 0, 0, 60)
            grad.setColorAt(0, QColor("#fdfc47")) # Amarelo claro topo
            grad.setColorAt(1, QColor("#ffd700")) # Amarelo ouro base
            self.setBrush(QBrush(grad))
        
        # Sombra lateral padrão (side shadow)
        if shadow is None:
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setOffset(5, 5)
            shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        
        # Configuração do Texto com wrapping e justificação
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setTextWidth(self.rect().width() - 20)  # Margens de 10px cada lado
        self.text_item.setPos(10, 10)
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        # Justificação do texto
        from PySide6.QtGui import QTextOption
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignJustify)
        text_option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.text_item.document().setDefaultTextOption(text_option)
        
        # Handles de redimensionamento
        self.handles = {p: Handle(self, p) for p in [
            'h1','h2','h3', 'h4', 'h5', 'h6','h7','h8'
        ]}
        self.update_handle_positions()
        self.set_handles_visible(False)
        
        # Para agrupamento
        self.group = None

    def resize_logic(self, pos_name, scene_pos):
        """Lógica de redimensionamento usando coordenadas da cena"""
        self.prepareGeometryChange()
        p_pos = self.mapToParent(self.mapFromScene(scene_pos))
        
        borda_esquerda = self.pos().x()
        borda_superior = self.pos().y()
        borda_direita = borda_esquerda + self.rect().width()
        borda_inferior = borda_superior + self.rect().height()

        new_x, new_y = borda_esquerda, borda_superior
        new_w, new_h = self.rect().width(), self.rect().height()

        if pos_name == 'h4': # Esquerda Centro
            new_x = p_pos.x()
            new_w = borda_direita - p_pos.x()
        elif pos_name == 'h5': # Direita Centro
            new_w = p_pos.x() - borda_esquerda
        elif pos_name == 'h2': # Topo Centro
            new_y = p_pos.y()
            new_h = borda_inferior - p_pos.y()
        elif pos_name == 'h7': # Base Centro
            new_h = p_pos.y() - borda_superior
        elif pos_name == 'h1': # Topo-Esquerda
            new_x, new_y = p_pos.x(), p_pos.y()
            new_w = borda_direita - p_pos.x()
            new_h = borda_inferior - p_pos.y()
        elif pos_name == 'h3': # Topo-Direita
            new_y = p_pos.y()
            new_w = p_pos.x() - borda_esquerda
            new_h = borda_inferior - p_pos.y()
        elif pos_name == 'h6': # Base-Esquerda
            new_x = p_pos.x()
            new_w = borda_direita - p_pos.x()
            new_h = p_pos.y() - borda_superior
        elif pos_name == 'h8': # Base-Direita
            new_w = p_pos.x() - borda_esquerda
            new_h = p_pos.y() - borda_superior

        if new_w < 50: new_w = 50
        if new_h < 30: new_h = 30

        self.setPos(new_x, new_y)
        super().setRect(0, 0, new_w, new_h)
        self.text_item.setTextWidth(max(50, new_w - 20))  # Mínimo de 50px de largura
        self.update_handle_positions()

    def update_handle_positions(self):
        r = self.rect()
        w, h = r.width(), r.height()
        self.handles['h1'].setPos(0, 0)
        self.handles['h2'].setPos(w/2, 0)
        self.handles['h3'].setPos(w, 0)
        self.handles['h4'].setPos(0, h/2)
        self.handles['h5'].setPos(w, h/2)
        self.handles['h6'].setPos(0, h)
        self.handles['h7'].setPos(w/2, h)
        self.handles['h8'].setPos(w, h)

    def set_handles_visible(self, visible):
        for h in self.handles.values():
            h.setVisible(visible)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.set_handles_visible(bool(value))
            if not bool(value):
                self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        
        if change == QGraphicsRectItem.ItemPositionChange:
            # Magnetismo / Alinhar: grid snap + alinhamento a objetos próximos (mesmo botão)
            main_win = QApplication.activeWindow()
            if hasattr(main_win, 'cb_magnetismo') and main_win.cb_magnetismo.isChecked():
                new_pos = value
                # Grid snap (magnetismo)
                grid = 20
                new_pos = QPointF(
                    round(new_pos.x() / grid) * grid,
                    round(new_pos.y() / grid) * grid
                )
                # Alinhamento a objetos próximos
                threshold = 15
                for item in self.scene().items():
                    if item != self and isinstance(item, StyledNode):
                        if abs(item.pos().x() - new_pos.x()) < threshold:
                            new_pos.setX(item.pos().x())
                        if abs(item.pos().y() - new_pos.y()) < threshold:
                            new_pos.setY(item.pos().y())
                return new_pos
        
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                try:
                    from core.connection import SmartConnection
                    for item in self.scene().items():
                        if isinstance(item, SmartConnection) and (item.source == self or item.target == self):
                            item.update_path()
                except: pass
        return super().itemChange(change, value)