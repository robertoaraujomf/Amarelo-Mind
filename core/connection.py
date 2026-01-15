from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import QLineF, Qt
from PySide6.QtGui import QPen, QColor

class SmartConnection(QGraphicsLineItem):
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
            
        # Conecta o centro do objeto A ao centro do objeto B
        line = QLineF(self.source.sceneBoundingRect().center(), 
                      self.target.sceneBoundingRect().center())
        self.setLine(line)

    def paint(self, painter, option, widget):
        self.update_path() # Força o ajuste da linha durante o movimento (ou snap do magnetismo)
        super().paint(painter, option, widget)