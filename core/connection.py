from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtGui import QPainterPath, QPen, QColor, QPainter
from PySide6.QtCore import Qt, QPointF, QRectF

class SmartConnection(QGraphicsPathItem):
    """
    Conexões curvas que desviam de objetos e mantêm distância mínima (Requisito 11).
    Implementa curvas de Bézier cúbicas e suporte a legendas (Requisito 13).
    """
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        
        # Estilo padrão: Grafite (Requisito 12: Cor editável)
        self.line_color = QColor("#444444")
        self.setPen(QPen(self.line_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        
        # Garante que as linhas fiquem atrás dos nós
        self.setZValue(-1)
        
        # Legenda opcional (Requisito 13)
        self.label = None
        
        self.update_path()

    def update_path(self):
        """Calcula a geometria da curva e desvia de nós no caminho"""
        if not self.source or not self.target:
            return

        path = QPainterPath()
        
        # Pontos centrais dos nós na cena
        p1 = self.source.sceneBoundingRect().center()
        p2 = self.target.sceneBoundingRect().center()
        
        path.moveTo(p1)
        
        # Ponto médio geográfico entre os dois nós
        mid_point = (p1 + p2) / 2
        
        # Lógica de Evasão (Requisito 11): 
        # Verifica se há objetos entre p1 e p2 para desviar
        search_rect = QRectF(p1, p2).normalized()
        
        # Offset padrão de desvio (aprox. 1cm ou 40-60 pixels)
        offset_y = 0
        
        if self.scene():
            # Busca itens no caminho
            items_in_way = self.scene().items(search_rect)
            for item in items_in_way:
                # Se encontrar um nó que NÃO seja a origem ou o destino
                if isinstance(item, QGraphicsRectItem) and item != self.source and item != self.target:
                    # Aplica desvio para cima para evitar sobreposição
                    offset_y = -70 
                    break

        # Pontos de controle para a Curva de Bézier Cúbica
        # Criamos uma curva suave em formato de 'S' ou arco
        ctrl1 = QPointF(mid_point.x(), p1.y() + offset_y)
        ctrl2 = QPointF(mid_point.x(), p2.y() + offset_y)
        
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)
        
        # Reposiciona a legenda se ela existir (Requisito 13)
        if self.label:
            # Coloca a legenda exatamente no meio (50%) da curva
            label_pos = path.pointAtPercent(0.5)
            self.label.setPos(label_pos)

    def set_label_text(self, text):
        """Cria ou atualiza a legenda da conexão"""
        if not self.label:
            self.label = QGraphicsTextItem(text, self)
            self.label.setDefaultTextColor(QColor("#1a1a1a"))
            # Aplica formatação básica
            font = self.label.font()
            font.setBold(True)
            self.label.setFont(font)
        else:
            self.label.setPlainText(text)
        self.update_path()

    # Dentro da classe SmartConnection
def update_path(self):
    # ... sua lógica existente de desenhar a linha ...
    super().setLine(self.source.sceneBoundingRect().center().x(), 
                    self.source.sceneBoundingRect().center().y(),
                    self.target.sceneBoundingRect().center().x(),
                    self.target.sceneBoundingRect().center().y())
    
    # Requisito 13: Se existir uma legenda, manda ela se reposicionar
    if hasattr(self, 'label') and self.label:
        self.label.update_position()
    def change_color(self, color_hex):
        """Altera a cor da linha (Requisito 12)"""
        self.line_color = QColor(color_hex)
        self.setPen(QPen(self.line_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        self.update()

def update_position(self):
        # ... seu código que calcula a linha entre source e target ...
        # Adicione isso ao final do método de movimento:
        if hasattr(self, 'label') and self.label:
            self.label.update_position()