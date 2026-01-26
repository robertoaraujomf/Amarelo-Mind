from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainter

class SmartConnection(QGraphicsPathItem):
    """Conexão curva ou reta entre objetos"""
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        # Azul conforme solicitado para o ícone de conexão
        self.setPen(QPen(QColor("#0078d4"), 3, Qt.SolidLine, Qt.RoundCap))
        self.setZValue(-1) # Garante que a linha fique por baixo dos nós
        self.update_path()

    def update_path(self):
        # Verifica se os objetos ainda existem na cena antes de calcular
        if not self.source.scene() or not self.target.scene():
            return
        
        source_center = self.source.sceneBoundingRect().center()
        target_center = self.target.sceneBoundingRect().center()
        
        # Calcula distância e direção
        dx = target_center.x() - source_center.x()
        dy = target_center.y() - source_center.y()
        distance = (dx**2 + dy**2)**0.5
        
        # Cria caminho curvo se necessário (quando objetos estão próximos ou sobrepostos)
        path = QPainterPath()
        path.moveTo(source_center)
        
        if distance < 100:  # Se muito próximos, usa curva
            # Curva suave com ponto de controle no meio
            control1 = QPointF(source_center.x() + dx * 0.5, source_center.y() - 30)
            control2 = QPointF(source_center.x() + dx * 0.5, target_center.y() + 30)
            path.cubicTo(control1, control2, target_center)
        else:
            # Linha reta com pequena curva se necessário para evitar sobreposição
            mid_x = (source_center.x() + target_center.x()) / 2
            mid_y = (source_center.y() + target_center.y()) / 2
            
            # Adiciona pequena curva se os objetos estão alinhados
            if abs(dy) < 20:  # Quase horizontal
                path.quadTo(QPointF(mid_x, mid_y - 20), target_center)
            elif abs(dx) < 20:  # Quase vertical
                path.quadTo(QPointF(mid_x - 20, mid_y), target_center)
            else:
                path.lineTo(target_center)
        
        self.setPath(path)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        self.update_path() # Força o ajuste da linha durante o movimento
        super().paint(painter, option, widget)