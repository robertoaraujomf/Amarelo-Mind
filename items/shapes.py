from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsTextItem
from PySide6.QtGui import QLinearGradient, QColor, QBrush, QPen, QPainter
from PySide6.QtCore import Qt, QRectF
from items.base_node import MindMapNode

class StyledNode(MindMapNode):
    def __init__(self, x, y):
        super().__init__(x, y)
        
        # 1. Configuração do Texto
        self.text_item.setPlaceholderText("Digite algo...")
        self.text_item.setDefaultTextColor(QColor("#2b2b2b"))
        
        # 2. Aplicar Sombra Profissional
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(5, 5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    def paint(self, painter, option, widget):
        """Sobrescreve o desenho para criar o gradiente e cantos arredondados"""
        # Configurar Gradiente Amarelo (Identidade da Marca)
        gradient = QLinearGradient(self.rect().topLeft(), self.rect().bottomLeft())
        gradient.setColorAt(0, QColor("#f2f71d")) # Amarelo vibrante
        gradient.setColorAt(1, QColor("#c3c910")) # Amarelo queimado
        
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Desenhar o corpo do nó
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#818511"), 2)) # Borda ocre
        painter.drawRoundedRect(self.rect(), 15, 15) # 15px de arredondamento

        # Se estiver selecionado, desenha uma borda de destaque
        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(-2, -2, 2, 2), 17, 17)

    def update_text_position(self):
        """Centraliza o texto conforme o nó é redimensionado"""
        r = self.rect()
        tr = self.text_item.boundingRect()
        self.text_item.setPos(
            r.center().x() - tr.width() / 2,
            r.center().y() - tr.height() / 2
        )