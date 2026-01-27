from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QColor, QBrush, QLinearGradient, QFont, QPen, QPainter
)
from .node_styles import NODE_COLORS, NODE_STATE


class StyledNode(QGraphicsRectItem):
    def __init__(self, x, y, w=200, h=100, node_type="Normal"):
        super().__init__(0, 0, w, h)

        self.setPos(x, y)
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )

        self.node_type = node_type
        self.has_shadow = True
        self.width = w
        self.height = h

        # Padrão: borda 0px, gradiente #ffff00 -> #e8e813
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor("#ffff00"))
        grad.setColorAt(1, QColor("#e8e813"))
        self.setBrush(QBrush(grad))
        self.setPen(QPen(Qt.NoPen))

        # Sombra ativa por padrão
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

        self.text = QGraphicsTextItem(self)
        self.text.setTextWidth(w - 20)
        self.text.setPos(10, 10)
        if node_type in ["Preto", "Azul", "Refutar"]:
            self.text.setDefaultTextColor(Qt.white)
        else:
            self.text.setDefaultTextColor(Qt.black)
        self.text.setFont(QFont("Segoe UI", 11))
        self.text.setTextInteractionFlags(Qt.TextEditorInteraction)

    # -------------------------------
    # CORES E ESTILOS
    # -------------------------------
    def update_color(self):
        """Atualiza a cor do nó baseado no tipo"""
        if self.node_type in NODE_COLORS:
            colors = NODE_COLORS[self.node_type]
            grad = QLinearGradient(0, 0, 0, self.height)
            grad.setColorAt(0, QColor(colors["light"]))
            grad.setColorAt(1, QColor(colors["dark"]))
            self.setBrush(QBrush(grad))

    def set_node_type(self, node_type):
        """Define o tipo do nó e atualiza sua aparência"""
        self.node_type = node_type
        self.update_color()
        
        # Atualiza cor do texto
        if node_type in ["Preto", "Azul", "Refutar"]:
            self.text.setDefaultTextColor(Qt.white)
        else:
            self.text.setDefaultTextColor(Qt.black)

    def toggle_shadow(self):
        """Ativa/desativa sombra"""
        if self.has_shadow:
            self.setGraphicsEffect(None)
            self.has_shadow = False
        else:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setOffset(2, 2)
            shadow.setColor(QColor(0, 0, 0, 100))
            self.setGraphicsEffect(shadow)
            self.has_shadow = True

    # -------------------------------
    # TEXTO
    # -------------------------------
    def get_text(self):
        return self.text.toPlainText()

    def set_text(self, txt):
        self.text.setPlainText(txt)

    def set_font(self, font):
        self.text.setFont(font)

    def set_background(self, color):
        grad = QLinearGradient(0, 0, 0, self.rect().height())
        grad.setColorAt(0, color.lighter(115))
        grad.setColorAt(1, color.darker(110))
        self.setBrush(QBrush(grad))

    # -------------------------------
    # CLONAGEM E MAGNETISMO
    # -------------------------------
    def clone_without_content(self):
        clone = StyledNode(self.x() + 30, self.y() + 30,
                           int(self.rect().width()), int(self.rect().height()),
                           self.node_type)
        clone.setBrush(self.brush())
        if self.graphicsEffect():
            clone.setGraphicsEffect(self.graphicsEffect())
        return clone

    # -------------------------------
    # MAGNETISMO
    # -------------------------------
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            main = QApplication.activeWindow()
            if hasattr(main, "alinhar_ativo") and main.alinhar_ativo:
                pos = value
                x = round(pos.x() / 20) * 20
                y = round(pos.y() / 20) * 20
                return pos.__class__(x, y)
        return super().itemChange(change, value)
