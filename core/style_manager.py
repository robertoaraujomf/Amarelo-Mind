from PySide6.QtWidgets import QColorDialog, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

class StyleManager:
    """Gerencia cores, sombras e efeitos visuais dos nós (Requisito 15)"""

    @staticmethod
    def change_background_color(parent, item):
        """Abre seletor de cores e aplica ao fundo do nó"""
        color = QColorDialog.getColor(item.brush().color(), parent, "Escolha a cor de fundo")
        if color.isValid():
            item.setBrush(color)

    @staticmethod
    def apply_shadow(item, blur=15, offset=5, color="#000000"):
        """Aplica ou ajusta a sombra do objeto para dar profundidade"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setOffset(offset)
        shadow.setColor(QColor(color))
        item.setGraphicsEffect(shadow)

    @staticmethod
    def set_gradient_style(item, color_start, color_end):
        """Prepara a estrutura para gradientes (base para animações futuras)"""
        # Aqui definiremos a lógica de gradiente linear/radial
        pass