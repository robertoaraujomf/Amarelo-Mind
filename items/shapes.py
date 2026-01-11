from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsTextItem
from PySide6.QtGui import QLinearGradient, QColor, QBrush, QPen, QPainter, QTextOption
from PySide6.QtCore import Qt, QRectF
from items.base_node import MindMapNode

class StyledNode(MindMapNode):
    def __init__(self, x, y):
        # 1. Atributos básicos
        self.padding = 20
        self.base_color = QColor("#f2f71d")
        
        super().__init__(x, y)
        
        if hasattr(self, 'text_item') and self.text_item:
            self.text_item.setDefaultTextColor(QColor("#1a1a1a"))
            
            # JUSTIFICAÇÃO
            option = QTextOption()
            option.setAlignment(Qt.Alignment(8)) 
            option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            self.text_item.document().setDefaultTextOption(option)
            
            font = self.text_item.font()
            font.setFamily("Segoe UI")
            font.setBold(True)
            font.setPointSize(10)
            self.text_item.setFont(font)

            # CONEXÃO: Objeto cresce enquanto você digita
            self.text_item.document().contentsChanged.connect(self.adjust_size_to_text)
            self.adjust_size_to_text()

        # Efeito de Sombra
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(15)
        self.shadow_effect.setOffset(4, 4)
        self.shadow_effect.setColor(QColor(0, 0, 0, 100))
        self.shadow_effect.setEnabled(True)
        self.setGraphicsEffect(self.shadow_effect)

    def center_text(self):
        """Centraliza o texto e aplica a largura para justificação"""
        if not hasattr(self, 'text_item') or not self.text_item:
            return
            
        r = self.rect()
        available_width = max(50, r.width() - (self.padding * 2))
        self.text_item.setTextWidth(available_width)
        
        tr = self.text_item.boundingRect()
        self.text_item.setPos(r.x() + (r.width() - tr.width()) / 2, 
                             r.y() + (r.height() - tr.height()) / 2)

    def adjust_size_to_text(self):
        """Redimensionamento automático para o texto nunca vazar"""
        if not hasattr(self, 'text_item') or not self.text_item:
            return

        curr_r = self.rect()
        tr = self.text_item.boundingRect()
        
        # Define o tamanho mínimo baseado no texto + padding
        min_w = tr.width() + (self.padding * 2)
        min_h = tr.height() + (self.padding * 2)
        
        # Só expande se o texto for maior que o retângulo atual
        new_w = max(curr_r.width(), min_w)
        new_h = max(curr_r.height(), min_h)
        
        if new_w != curr_r.width() or new_h != curr_r.height():
            self.prepareGeometryChange()
            # IMPORTANTE: super().setRect ignora a trava e aplica o tamanho
            super().setRect(0, 0, new_w, new_h)
            if hasattr(self, 'update_handle_positions'):
                self.update_handle_positions()
        
        self.center_text()

    def setRect(self, *args):
        """
        Aceita tanto setRect(x, y, w, h) quanto setRect(QRectF).
        Isso resolve o erro de 'missing positional arguments'.
        """
        if len(args) == 1 and isinstance(args[0], QRectF):
            rect = args[0]
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        elif len(args) == 4:
            x, y, w, h = args
        else:
            # Fallback para o comportamento padrão do Qt
            super().setRect(*args)
            return

        # Trava de tamanho mínimo: impede o usuário de "esmagar" o texto
        if hasattr(self, 'text_item') and self.text_item:
            tr = self.text_item.boundingRect()
            min_w = tr.width() + (self.padding * 2)
            min_h = tr.height() + (self.padding * 2)
            w = max(w, min_w)
            h = max(h, min_h)
            
        super().setRect(x, y, w, h)
        self.center_text()

    def paint(self, painter, option, widget):
        r = self.rect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0, self.base_color)
        gradient.setColorAt(1, self.base_color.darker(115))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(r, 12, 12)

        if self.isSelected():
            painter.setPen(QPen(QColor("#ffffff"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r.adjusted(-3, -3, 3, 3), 14, 14)

    def itemChange(self, change, value):
        return super().itemChange(change, value)

class EllipseNode(StyledNode):
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