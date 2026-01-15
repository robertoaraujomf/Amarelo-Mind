from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QApplication
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QLinearGradient

class StyledNode(QGraphicsRectItem):
    # Alteramos para aceitar um brush opcional (para o recurso de clonar cor)
    def __init__(self, x, y, text="", brush=None):
        super().__init__(0, 0, 160, 60)
        self.setPos(x, y)
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                      QGraphicsRectItem.ItemIsSelectable | 
                      QGraphicsRectItem.ItemSendsGeometryChanges)
        
        # Lógica de Cor: Se não houver brush, aplica o degradê amarelo padrão
        if brush:
            self.setBrush(brush)
        else:
            grad = QLinearGradient(0, 0, 0, 60)
            grad.setColorAt(0, QColor("#fdfc47")) # Amarelo claro topo
            grad.setColorAt(1, QColor("#ffd700")) # Amarelo ouro base
            self.setBrush(QBrush(grad))
            
        self.setPen(QPen(QColor("#333"), 2))
        
        # Configuração do Texto (vazio por padrão para novos objetos)
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setPos(10, 15)
        # Permite edição mas o foco será controlado pela main.py
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            # Magnetismo vinculado à checkbox da Main
            main_win = QApplication.activeWindow()
            if hasattr(main_win, 'cb_magnetismo') and main_win.cb_magnetismo.isChecked():
                grid = 20
                new_pos = value
                x = round(new_pos.x() / grid) * grid
                y = round(new_pos.y() / grid) * grid
                return QPointF(x, y)
        return super().itemChange(change, value)