from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QLinearGradient, QColor, QBrush, QPen, QPainter, QRadialGradient
from PySide6.QtCore import Qt, QRectF
from items.base_node import MindMapNode

class StyledNode(MindMapNode):
    def __init__(self, x, y):
        super().__init__(x, y)
        
        # Cor base padrão (Amarelo original)
        self.base_color = QColor("#f2f71d")
        
        # Configuração de Texto
        self.text_item.setDefaultTextColor(QColor("#1a1a1a"))
        font = self.text_item.font()
        font.setFamily("Segoe UI")
        font.setBold(True)
        font.setPointSize(10)
        self.text_item.setFont(font)
        
        # Sombra (Requisito 12)
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(15)
        self.shadow_effect.setOffset(4, 4)
        self.shadow_effect.setColor(QColor(0, 0, 0, 100))
        self.shadow_effect.setEnabled(True) # Começa com sombra
        self.setGraphicsEffect(self.shadow_effect)
        
        self.padding = 5 

    def set_custom_color(self, color):
        """ITEM 10: Altera a cor mantendo a lógica de degradê"""
        self.base_color = color
        self.update() # Força o repaint com a nova cor

    def toggle_shadow(self):
        """ITEM 12: Liga/Desliga o efeito de sombra"""
        effect = self.graphicsEffect()
        if effect:
            effect.setEnabled(not effect.isEnabled())

    def paint(self, painter, option, widget):
        """Aplica o design com a cor dinâmica base_color"""
        r = self.rect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # ITEM 10: Gradiente baseado na base_color (escolhida pelo usuário ou padrão)
        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0, self.base_color) # Cor escolhida
        gradient.setColorAt(1, self.base_color.darker(115)) # Tom mais escuro para o degradê
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        
        # Vértices arredondados
        painter.drawRoundedRect(r, 12, 12)

        # Feedback Visual de Seleção
        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r.adjusted(-3, -3, 3, 3), 14, 14)

class EllipseNode(StyledNode):
    """Variação elíptica do nó"""
    def paint(self, painter, option, widget):
        r = self.rect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0, self.base_color)
        gradient.setColorAt(1, self.base_color.darker(115))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        
        painter.drawEllipse(r)

        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(r.adjusted(-3, -3, 3, 3))

    def center_text(self):
        r = self.rect()
        tr = self.text_item.boundingRect()
        self.text_item.setPos(r.center().x() - tr.width()/2, 
                             r.center().y() - tr.height()/2)
        
        if tr.width() + 40 > r.width() or tr.height() + 40 > r.height():
            new_dim = max(r.width(), tr.width() + 40, r.height(), tr.height() + 40)
            self.setRect(0, 0, new_dim, new_dim)
            self.update_handle_positions()