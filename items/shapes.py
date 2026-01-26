from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QApplication
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QColor, QBrush, QLinearGradient, QFont
)


class StyledNode(QGraphicsRectItem):
    def __init__(self, x, y, w=200, h=100):
        super().__init__(0, 0, w, h)

        self.setPos(x, y)
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )

        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor("#fff3b0"))
        gradient.setColorAt(1, QColor("#f5c542"))
        self.setBrush(QBrush(gradient))
        self.setPen(Qt.NoPen)

        self.text = QGraphicsTextItem(self)
        self.text.setTextWidth(w - 20)
        self.text.setPos(10, 10)
        self.text.setDefaultTextColor(Qt.black)
        self.text.setFont(QFont("Segoe UI", 11))
        self.text.setTextInteractionFlags(Qt.TextEditorInteraction)

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

    def clone_without_content(self):
        clone = StyledNode(self.x() + 30, self.y() + 30,
                           self.rect().width(), self.rect().height())
        clone.setBrush(self.brush())
        if self.graphicsEffect():
            clone.setGraphicsEffect(self.graphicsEffect())
        return clone

    # -------------------------------
    # MAGNETISMO (CORRIGIDO)
    # -------------------------------
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            main = QApplication.activeWindow()
            if hasattr(main, "magnetismo_ativo") and main.magnetismo_ativo:
                pos = value
                x = round(pos.x() / 20) * 20
                y = round(pos.y() / 20) * 20
                return pos.__class__(x, y)
        return super().itemChange(change, value)
