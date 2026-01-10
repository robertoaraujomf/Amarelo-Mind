from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QLinearGradient, QColor, QBrush, QPen, QPainter
from PySide6.QtCore import Qt, QRectF
from items.base_node import MindMapNode

class StyledNode(MindMapNode):
    def __init__(self, x, y):
        super().__init__(x, y)
        
        # Requisito 14/15: Formatação de texto padrão (Negrito/Segoe UI)
        self.text_item.setDefaultTextColor(QColor("#1a1a1a"))
        font = self.text_item.font()
        font.setFamily("Segoe UI")
        font.setBold(True)
        font.setPointSize(10)
        self.text_item.setFont(font)
        
        # Requisito: Sem borda por padrão, apenas sombra
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(4, 4)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(self.shadow)
        
        # Margem interna padrão (Padding) - Requisito 16 (0.2mm aprox 2-3px)
        self.padding = 5 

    def paint(self, painter, option, widget):
        """Aplica o design moderno com gradientes e curvas"""
        r = self.rect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Requisito 15: Efeito Gradiente
        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0, QColor("#f2f71d")) # Amarelo vibrante
        gradient.setColorAt(1, QColor("#d4d912")) # Amarelo ouro
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen) # Requisito: Sem borda por padrão
        
        # Requisito: Vértices arredondados
        painter.drawRoundedRect(r, 12, 12)

        # Feedback Visual de Seleção
        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r.adjusted(-3, -3, 3, 3), 14, 14)

class EllipseNode(StyledNode):
    """Variação elíptica do nó de mapa mental"""
    def paint(self, painter, option, widget):
        r = self.rect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0, QColor("#f2f71d"))
        gradient.setColorAt(1, QColor("#d4d912"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        
        # Desenha Elipse em vez de Retângulo
        painter.drawEllipse(r)

        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(r.adjusted(-3, -3, 3, 3))

    def center_text(self):
        """Ajuste específico para texto dentro de elipses (mais padding)"""
        r = self.rect()
        tr = self.text_item.boundingRect()
        # Elipses precisam de mais margem para o texto não bater nas bordas curvas
        self.text_item.setPos(r.center().x() - tr.width()/2, 
                             r.center().y() - tr.height()/2)
        
        if tr.width() + 40 > r.width() or tr.height() + 40 > r.height():
            new_dim = max(r.width(), tr.width() + 40, r.height(), tr.height() + 40)
            self.setRect(0, 0, new_dim, new_dim)
            self.update_handle_positions()