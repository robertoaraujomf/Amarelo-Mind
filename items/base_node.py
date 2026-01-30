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
        # self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setZValue(100)
        
        cursors = {
            'h1': Qt.SizeFDiagCursor, 'h3': Qt.SizeBDiagCursor,
            'h6': Qt.SizeBDiagCursor, 'h8': Qt.SizeFDiagCursor,
            'h2': Qt.SizeVerCursor,   'h7': Qt.SizeVerCursor,
            'h4': Qt.SizeHorCursor,   'h5': Qt.SizeHorCursor
        }
        self.setCursor(cursors.get(position_name, Qt.ArrowCursor))

    def mousePressEvent(self, event):
        event.accept()

    def mouseMoveEvent(self, event):
        # Usamos a posição global do mouse (ScenePos) para evitar o loop de movimento relativo
        self.parent_node.resize_logic(self.pos_name, event.scenePos())

    def mouseReleaseEvent(self, event):
        event.accept()

class MindMapNode(QGraphicsRectItem):
    """Objeto Nó com redimensionamento livre por coordenadas de cena"""
    def __init__(self, x, y):
        super().__init__(0, 0, 150, 80)
        self.setPos(x, y)
        
        self.text_item = QGraphicsTextItem("Novo Objeto", self)
        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        
        # Garante que o texto não "vaze" para fora do objeto se ele for muito pequeno
        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape, True)
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        self.handles = {p: Handle(self, p) for p in [
            'h1','h2','h3', 'h4', 'h5', 'h6','h7','h8'
        ]}
        
        self.update_handle_positions()
        self.set_handles_visible(False)

    def resize_logic(self, pos_name, scene_pos):
        """
        Lógica de redimensionamento livre usando a cena como referencial.
        Isso impede que o objeto seja 'arrastado' ao diminuir.
        """
        self.prepareGeometryChange()
        
        # Converte a posição atual do mouse na cena para o sistema do PAI do objeto
        # (Se o objeto está na cena, p_pos será a coord da cena)
        p_pos = self.mapToParent(self.mapFromScene(scene_pos))
        
        # Geometria atual em relação ao pai
        curr_rect = self.sceneBoundingRect() # Coordenadas globais
        # Se houver um pai que não seja a cena, usamos mapToParent
        # Mas para simplificar, usaremos as bordas fixas no sistema do pai:
        
        # Pegamos as bordas atuais antes da mudança
        borda_esquerda = self.pos().x()
        borda_superior = self.pos().y()
        borda_direita = borda_esquerda + self.rect().width()
        borda_inferior = borda_superior + self.rect().height()

        new_x, new_y = borda_esquerda, borda_superior
        new_w, new_h = self.rect().width(), self.rect().height()

        # Lógica de cálculo baseada na borda oposta fixa
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

        # Prevenção de largura/altura negativa (opcional, mas evita erros visuais)
        if new_w < 5: new_w = 5
        if new_h < 5: new_h = 5

        # Aplicamos as novas coordenadas
        self.setPos(new_x, new_y)
        super().setRect(0, 0, new_w, new_h)
        
        # Atualizamos o conteúdo
        self.text_item.setTextWidth(new_w)
        self.center_text()
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

    def center_text(self):
        r = self.rect()
        tr = self.text_item.boundingRect()
        self.text_item.setPos((r.width() - tr.width()) / 2, 
                             (r.height() - tr.height()) / 2)

    def set_handles_visible(self, visible):
        for h in self.handles.values(): h.setVisible(visible)

    def mouseDoubleClickEvent(self, event):
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setFocus()
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.set_handles_visible(bool(value))
            if not bool(value):
                self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                try:
                    from core.connection import SmartConnection
                    for item in self.scene().items():
                        if isinstance(item, SmartConnection) and (item.source == self or item.target == self):
                            item.update_path()
                except: pass
        return super().itemChange(change, value)