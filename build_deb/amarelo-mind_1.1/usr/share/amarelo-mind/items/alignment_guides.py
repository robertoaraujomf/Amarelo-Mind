from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsScene
from PySide6.QtCore import Qt, QLineF, QPointF
from PySide6.QtGui import QPen, QColor


class AlignmentGuide(QGraphicsLineItem):
    """Linha de guia para alinhamento visual"""
    def __init__(self, line, scene=None):
        super().__init__(line)
        self.setPen(QPen(QColor(100, 150, 255, 100), 1, Qt.DashLine))
        self.setZValue(-1)
        if scene:
            scene.addItem(self)


class AlignmentGuidesManager:
    """Gerencia as linhas de alinhamento visual"""
    
    SNAP_THRESHOLD = 10  # pixels para considerar alinhado
    
    def __init__(self, scene):
        self.scene = scene
        self.guides = []
    
    def clear_guides(self):
        """Remove todas as linhas de guia"""
        for guide in self.guides:
            self.scene.removeItem(guide)
        self.guides = []
    
    def get_alignment_lines(self, moving_item):
        """Calcula as linhas de alinhamento para um item em movimento"""
        lines = []
        
        moving_rect = moving_item.sceneBoundingRect()
        moving_left = moving_rect.left()
        moving_right = moving_rect.right()
        moving_top = moving_rect.top()
        moving_bottom = moving_rect.bottom()
        moving_center_x = moving_rect.center().x()
        moving_center_y = moving_rect.center().y()
        
        # Coletar todos os itens para comparação
        other_items = [item for item in self.scene.items() if item != moving_item and hasattr(item, 'sceneBoundingRect')]
        
        for other_item in other_items:
            other_rect = other_item.sceneBoundingRect()
            other_left = other_rect.left()
            other_right = other_rect.right()
            other_top = other_rect.top()
            other_bottom = other_rect.bottom()
            other_center_x = other_rect.center().x()
            other_center_y = other_rect.center().y()
            
            # Alinhamento VERTICAL (esquerda)
            if abs(moving_left - other_left) < self.SNAP_THRESHOLD:
                x = moving_left
                scene_rect = self.scene.sceneRect()
                line = QLineF(x, scene_rect.top(), x, scene_rect.bottom())
                lines.append(line)
            
            # Alinhamento VERTICAL (direita)
            if abs(moving_right - other_right) < self.SNAP_THRESHOLD:
                x = moving_right
                scene_rect = self.scene.sceneRect()
                line = QLineF(x, scene_rect.top(), x, scene_rect.bottom())
                lines.append(line)
            
            # Alinhamento VERTICAL (centro)
            if abs(moving_center_x - other_center_x) < self.SNAP_THRESHOLD:
                x = moving_center_x
                scene_rect = self.scene.sceneRect()
                line = QLineF(x, scene_rect.top(), x, scene_rect.bottom())
                lines.append(line)
            
            # Alinhamento HORIZONTAL (topo)
            if abs(moving_top - other_top) < self.SNAP_THRESHOLD:
                y = moving_top
                scene_rect = self.scene.sceneRect()
                line = QLineF(scene_rect.left(), y, scene_rect.right(), y)
                lines.append(line)
            
            # Alinhamento HORIZONTAL (base)
            if abs(moving_bottom - other_bottom) < self.SNAP_THRESHOLD:
                y = moving_bottom
                scene_rect = self.scene.sceneRect()
                line = QLineF(scene_rect.left(), y, scene_rect.right(), y)
                lines.append(line)
            
            # Alinhamento HORIZONTAL (centro)
            if abs(moving_center_y - other_center_y) < self.SNAP_THRESHOLD:
                y = moving_center_y
                scene_rect = self.scene.sceneRect()
                line = QLineF(scene_rect.left(), y, scene_rect.right(), y)
                lines.append(line)
        
        return lines
    
    def show_guides(self, moving_item):
        """Exibe as linhas de guia para um item"""
        self.clear_guides()
        lines = self.get_alignment_lines(moving_item)
        
        for line in lines:
            guide = AlignmentGuide(line, self.scene)
            self.guides.append(guide)
