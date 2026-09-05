import sys
import os
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QToolBar, QFileDialog, QFrame, QFontDialog, QColorDialog,
    QMessageBox, QGraphicsTextItem, QDialog, QInputDialog,
    QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
)
from PySide6.QtCore import Qt, QSize, QPointF, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QAction, QWheelEvent,
    QUndoStack, QImage, QUndoCommand, QFont,
    QTextCursor, QTextCharFormat, QPen, QPixmap,
    QTextOption
)

# ======================================================
# PATHS / ÍCONES
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from core.icon_manager import IconManager
from core.persistence import PersistenceManager
from core.item_filter import ItemFilter
from core.positioning import find_best_position_radial
from core.dialogs import FontStyleDialog, ColorPickerDialog
IconManager.set_icons_base(BASE_DIR)

from items.shapes import StyledNode, Handle
from items.group_item import GroupNode
from core.connection import SmartConnection
from items.alignment_guides import AlignmentGuidesManager
from items.media import MediaItem
from items.media import MediaImageItem
from items.media import MediaSliderImageItem
from items.media import MediaAVItem
from items.media import MediaAVSliderItem
import urllib.request


# ======================================================
# TEMAS
# ======================================================
THEMES = {
    "Padrão": {
        "primary": "#2d6a4f",
        "primary_light": "#3d7a5f",
        "primary_dark": "#1d5a3f",
        "primary_darker": "#0d4a2f",
        "bg_main": "#0f1621",
        "bg_toolbar": "#1a2332",
        "border": "#2d3a4f",
        "border_light": "#3d4a5f",
        "text": "#c0c8d8",
        "text_light": "#f0f6fc",
        "accent": "#90EE90",
        "scrollbar": "#2d3a4f",
        "scrollbar_hover": "#4d5a6f",
        "disabled": "#666666",
        "canvas_bg": "#0f1621",
    },
    "#661f41": {
        "primary": "#661f41",
        "primary_light": "#7d2a52",
        "primary_dark": "#4f1732",
        "primary_darker": "#3a0f25",
        "bg_main": "#1a0e14",
        "bg_toolbar": "#23141c",
        "border": "#3a2030",
        "border_light": "#4a3040",
        "text": "#d8c0c8",
        "text_light": "#fcf0f4",
        "accent": "#FFB6C1",
        "scrollbar": "#3a2030",
        "scrollbar_hover": "#5a4050",
        "disabled": "#665555",
        "canvas_bg": "#1a0e14",
    },
    "#11799e": {
        "primary": "#11799e",
        "primary_light": "#1a8fb8",
        "primary_dark": "#0d6080",
        "primary_darker": "#084a60",
        "bg_main": "#0a1a22",
        "bg_toolbar": "#0f2530",
        "border": "#1a4050",
        "border_light": "#2a5565",
        "text": "#b0d8e8",
        "text_light": "#e0f4fc",
        "accent": "#70d0f0",
        "scrollbar": "#1a4050",
        "scrollbar_hover": "#2a5565",
        "disabled": "#4a6a7a",
        "canvas_bg": "#0a1a22",
    },
    "#dabbed": {
        "primary": "#b07090",
        "primary_light": "#c080a0",
        "primary_dark": "#9a6080",
        "primary_darker": "#805068",
        "bg_main": "#1a1018",
        "bg_toolbar": "#231820",
        "border": "#382535",
        "border_light": "#483545",
        "text": "#d8c0d0",
        "text_light": "#fcf0f8",
        "accent": "#dabbed",
        "scrollbar": "#382535",
        "scrollbar_hover": "#584555",
        "disabled": "#665566",
        "canvas_bg": "#1a1018",
    },
}

def generate_qss(theme):
    """Gera o QSS a partir do template e do dicionário de cores do tema."""
    qss_path = os.path.join(BASE_DIR, "assets", "styles.qss")
    if not os.path.exists(qss_path):
        return ""
    with open(qss_path, "r", encoding="utf-8") as f:
        qss = f.read()
    replacements = {
        "{{PRIMARY}}": theme["primary"],
        "{{PRIMARY_LIGHT}}": theme["primary_light"],
        "{{PRIMARY_DARK}}": theme["primary_dark"],
        "{{PRIMARY_DARKER}}": theme["primary_darker"],
        "{{BG_MAIN}}": theme["bg_main"],
        "{{BG_TOOLBAR}}": theme["bg_toolbar"],
        "{{BORDER}}": theme["border"],
        "{{BORDER_LIGHT}}": theme["border_light"],
        "{{TEXT}}": theme["text"],
        "{{TEXT_LIGHT}}": theme["text_light"],
        "{{ACCENT}}": theme["accent"],
        "{{SCROLLBAR}}": theme["scrollbar"],
        "{{SCROLLBAR_HOVER}}": theme["scrollbar_hover"],
        "{{DISABLED}}": theme["disabled"],
    }
    for placeholder, color in replacements.items():
        qss = qss.replace(placeholder, color)
    return qss


# ======================================================
# COMANDOS UNDO/REDO
# ======================================================
class ChangeNodeStyleCommand(QUndoCommand):
    """Comando para alterar o estilo/cor de fundo de um nó"""
    def __init__(self, item, old_state, new_state, description="Alterar estilo"):
        super().__init__(description)
        self.item = item
        self.old_state = old_state
        self.new_state = new_state

    def redo(self):
        self._apply_state(self.new_state)

    def undo(self):
        self._apply_state(self.old_state)

    def _apply_state(self, state):
        self.item.node_type = state['node_type']
        if state['custom_color']:
            self.item.set_background(QColor(state['custom_color']))
        else:
            self.item.set_node_type(state['node_type'])


class ChangeTextHtmlCommand(QUndoCommand):
    """Comando para alterar o texto/estilo (HTML) de um nó"""
    def __init__(self, item, old_html, new_html, description="Alterar texto"):
        super().__init__(description)
        self.item = item
        self.old_html = old_html
        self.new_html = new_html

    def redo(self):
        self.item.text.setHtml(self.new_html)
        # Forçar atualização da fonte do widget baseada no HTML
        self._update_font_from_html(self.new_html)

    def undo(self):
        self.item.text.setHtml(self.old_html)
        # Forçar atualização da fonte do widget baseada no HTML
        self._update_font_from_html(self.old_html)
    
    def _update_font_from_html(self, html):
        """Extrai informações de fonte do HTML e aplica ao widget"""
        from PySide6.QtGui import QTextDocument, QFontDatabase
        import re
        
        # Procurar por informações de fonte no estilo do body
        body_style_match = re.search(r'<body[^>]*style="[^"]*font-family:([^;]+);[^"]*font-size:(\d+)pt', html)
        if body_style_match:
            family = body_style_match.group(1).strip('\'"')
            size = int(body_style_match.group(2))
            
            # Aplicar ao widget
            current_font = self.item.text.font()
            current_font.setFamily(family)
            current_font.setPointSize(size)
            self.item.text.setFont(current_font)


class ChangeFontCommand(QUndoCommand):
    """Comando para alterar a fonte de um nó (propriedade)"""
    def __init__(self, item, old_font, new_font, description="Alterar fonte"):
        super().__init__(description)
        self.item = item
        self.old_font = old_font
        self.new_font = new_font

    def redo(self):
        self.item.set_font(self.new_font)

    def undo(self):
        self.item.set_font(self.old_font)


class AddItemCommand(QUndoCommand):
    """Comando para adicionar um item à cena"""
    def __init__(self, scene, item, description="Adicionar objeto", window=None):
        super().__init__(description)
        self.scene = scene
        self.item = item
        self.window = window

    def redo(self):
        self.scene.addItem(self.item)
        if isinstance(self.item, StyledNode) and self.window:
            if hasattr(self.item.text, 'selectionChanged'):
                self.item.text.selectionChanged.connect(self.window.update_button_states)
        # Se for uma conexão, atualizar o caminho
        if hasattr(self.item, 'update_path'):
            self.item.update_path()

    def undo(self):
        self.scene.removeItem(self.item)


class RemoveItemCommand(QUndoCommand):
    """Comando para remover um item da cena"""
    def __init__(self, scene, item, description="Remover objeto"):
        super().__init__(description)
        self.scene = scene
        self.item = item
        # Parar mídia se for um item de mídia
        if hasattr(item, 'stop_video'):
            item.stop_video()

    def redo(self):
        self.scene.removeItem(self.item)

    def undo(self):
        self.scene.addItem(self.item)


class SplitMapCommand(QUndoCommand):
    """Move um subgrafo (objeto selecionado + descendentes) para uma nova janela.

    Suporta desfazer/refazer: undo devolve os objetos ao mapa de origem e
    restaura as conexões de contorno; redo os transfere novamente para o
    mapa destino (a nova janela, onde o objeto selecionado vira título).
    """
    def __init__(self, source_scene, target_scene, target_window, nodes,
                 conns_moved, conns_dropped, root):
        super().__init__("Desmembrar mapa mental")
        self.source_scene = source_scene
        self.target_scene = target_scene
        self.target_window = target_window  # Mantém a nova janela viva
        self.nodes = nodes
        self.conns_moved = conns_moved
        self.conns_dropped = conns_dropped
        self.root = root
        self.is_styled_root = isinstance(root, StyledNode)
        self.applied_title = False

    def redo(self):
        # Remover do mapa de origem
        for conn in self.conns_moved + self.conns_dropped:
            if conn.scene() is self.source_scene:
                self.source_scene.removeItem(conn)
        for item in self.nodes:
            if item.scene() is self.source_scene:
                self.source_scene.removeItem(item)
        # Adicionar ao mapa destino
        for item in self.nodes:
            if item.scene() is not self.target_scene:
                self.target_scene.addItem(item)
        for conn in self.conns_moved:
            if conn.scene() is not self.target_scene:
                self.target_scene.addItem(conn)
            conn.update_path()
        # O objeto selecionado torna-se o título do novo mapa
        if self.is_styled_root and not self.root._is_title:
            self.root.set_is_title(True)
            self.applied_title = True

    def undo(self):
        # Reverter o estado de título do objeto selecionado
        if self.applied_title and self.root._is_title:
            self.root.set_is_title(False)
            self.applied_title = False
        # Remover do mapa destino
        for conn in self.conns_moved:
            if conn.scene() is self.target_scene:
                self.target_scene.removeItem(conn)
        for item in self.nodes:
            if item.scene() is self.target_scene:
                self.target_scene.removeItem(item)
        # Devolver ao mapa de origem
        for item in self.nodes:
            if item.scene() is not self.source_scene:
                self.source_scene.addItem(item)
        for conn in self.conns_moved + self.conns_dropped:
            if conn.scene() is not self.source_scene:
                self.source_scene.addItem(conn)
            conn.update_path()


class PasteTextCommand(QUndoCommand):
    """Comando para colar texto em um nó"""
    def __init__(self, node, old_html, new_html, description="Colar texto"):
        super().__init__(description)
        self.node = node
        self.old_html = old_html
        self.new_html = new_html

    def redo(self):
        self.node.text.setHtml(self.new_html)

    def undo(self):
        self.node.text.setHtml(self.old_html)


class MoveItemCommand(QUndoCommand):
    """Comando para mover um item na cena"""
    def __init__(self, item, old_pos, new_pos, description="Mover objeto"):
        super().__init__(description)
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.item.prepareGeometryChange()
        self.item.setPos(self.new_pos)
        self._update_connections()
        if self.item.scene():
            self.item.scene().update()

    def undo(self):
        self.item.prepareGeometryChange()
        self.item.setPos(self.old_pos)
        self._update_connections()
        if self.item.scene():
            self.item.scene().update()
    
    def _update_connections(self):
        if self.item.scene():
            try:
                from core.connection import SmartConnection
                for conn in self.item.scene().items():
                    if isinstance(conn, SmartConnection) and (conn.source == self.item or conn.target == self.item):
                        conn.update_path()
            except:
                pass

class ReplaceMediaCommand(QUndoCommand):
    """Comando para substituir um item de mídia por outro"""
    def __init__(self, scene, old_item, new_item, description="Substituir mídia"):
        super().__init__(description)
        self.scene = scene
        self.old_item = old_item
        self.new_item = new_item
        self.new_item.setPos(old_item.pos())

    def redo(self):
        if self.old_item.scene():
            self.scene.removeItem(self.old_item)
        if not self.new_item.scene():
            self.scene.addItem(self.new_item)
        self.new_item.setPos(self.old_item.pos())

    def undo(self):
        if self.new_item.scene():
            self.scene.removeItem(self.new_item)
        if not self.old_item.scene():
            self.scene.addItem(self.old_item)


class ToggleShadowCommand(QUndoCommand):
    """Comando para desfazer/refazer toggle de sombra"""
    def __init__(self, items):
        super().__init__("Alternar sombra")
        self.items = items
        self.old_states = []
        for item in items:
            self.old_states.append({
                'has_shadow': item.has_shadow,
                'effect': item.graphicsEffect()
            })

    def redo(self):
        for item in self.items:
            item.toggle_shadow()

    def undo(self):
        for i, item in enumerate(self.items):
            state = self.old_states[i]
            if state['has_shadow'] and not item.has_shadow:
                item.toggle_shadow()
            elif not state['has_shadow'] and item.has_shadow:
                item.toggle_shadow()


class ApplyStyleFilteredCommand(QUndoCommand):
    """Comando para desfazer/refazer aplicação de estilo a itens filtrados"""
    def __init__(self, items, new_style, scene):
        super().__init__("Aplicar estilo")
        self.items = items
        self.new_style = new_style
        self.scene = scene
        self.old_states = []
        for item in items:
            self.old_states.append({
                'node_type': item.node_type,
                'custom_color': item.custom_color
            })

    def redo(self):
        for item in self.items:
            item.set_node_type(self.new_style)
            item.update_brush()

    def undo(self):
        for i, item in enumerate(self.items):
            state = self.old_states[i]
            item.node_type = state['node_type']
            item.custom_color = state['custom_color']
            item.update_brush()



# ======================================================
# CANVAS INFINITO
# ======================================================
class InfiniteCanvas(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

        # Otimizações de renderização para melhor performance
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform
        )

        # Otimização de cache para items estáticos
        self.setCacheMode(QGraphicsView.CacheBackground)
        
        self.setBackgroundBrush(QColor("#0f1621"))
        self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # Melhorar performance com update otimizado
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # essencial para seleção retangular
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)

        self._panning = False
        self._last_pos = None
        self.undo_stack = None
        self._item_positions = {}  # Rastreia posições originais para Undo/Redo
        self.alignment_guides = AlignmentGuidesManager(scene)
        self._moving_item = None
        
        # Sistema de drag para conexões
        self._dragging_connection = False
        self._dragged_connection = None
        self._drag_offset = QPointF()
        
        # Sistema de drag para itens (evita mover apenas com clique)
        self._dragging_item = None
        self._drag_start_pos = None
        self._is_dragging = False
        
        # Configurar scrollbars com alcance expandido
        self._setup_expanded_scrollbars()
    
    def _setup_expanded_scrollbars(self):
        """Configura scrollbars com alcance expandido para canvas infinito"""
        h_scroll = self.horizontalScrollBar()
        v_scroll = self.verticalScrollBar()
        h_scroll.setRange(-100000, 100000)
        v_scroll.setRange(-100000, 100000)
    
    def _extend_scroll_range_if_needed(self):
        """Estende o alcance dos scrollbars dinamicamente se necessário"""
        h_scroll = self.horizontalScrollBar()
        v_scroll = self.verticalScrollBar()
        current_min_h, current_max_h = h_scroll.minimum(), h_scroll.maximum()
        current_min_v, current_max_v = v_scroll.minimum(), v_scroll.maximum()
        
        val_h = h_scroll.value()
        val_v = v_scroll.value()
        
        new_min_h, new_max_h = current_min_h, current_max_h
        new_min_v, new_max_v = current_min_v, current_max_v
        
        if val_h < current_min_h + 1000:
            new_min_h = current_min_h - 50000
        if val_h > current_max_h - 1000:
            new_max_h = current_max_h + 50000
        if val_v < current_min_v + 1000:
            new_min_v = current_min_v - 50000
        if val_v > current_max_v - 1000:
            new_max_v = current_max_v + 50000
        
        if (new_min_h != current_min_h or new_max_h != current_max_h or
            new_min_v != current_min_v or new_max_v != current_max_v):
            h_scroll.setRange(new_min_h, new_max_h)
            v_scroll.setRange(new_min_v, new_max_v)

    def set_undo_stack(self, undo_stack):
        """Define o stack de Undo/Redo"""
        self.undo_stack = undo_stack

    def keyPressEvent(self, event):
        """Movimento com setas (10 px) para itens selecionados ou pan da tela.
        Durante edição de texto de um nó, as teclas vão para o editor."""
        focus_item = self.scene().focusItem()
        if isinstance(focus_item, QGraphicsTextItem) and \
           (focus_item.textInteractionFlags() & Qt.TextEditable):
            super().keyPressEvent(event)
            return

        key = event.key()
        if key not in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            super().keyPressEvent(event)
            return

        step = 10
        delta = {Qt.Key_Left: QPointF(-step, 0),
                 Qt.Key_Right: QPointF(step, 0),
                 Qt.Key_Up: QPointF(0, -step),
                 Qt.Key_Down: QPointF(0, step)}[key]

        selected = [it for it in self.scene().selectedItems()
                    if isinstance(it, (StyledNode, MediaItem))]
        if selected:
            for item in selected:
                item.setPos(item.pos() + delta)
        else:
            # Pan da tela usando as scrollbars
            h_scroll = self.horizontalScrollBar()
            v_scroll = self.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() + int(delta.x()))
            v_scroll.setValue(v_scroll.value() + int(delta.y()))
            self._extend_scroll_range_if_needed()
        event.accept()

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        """
        Controle do mouse otimizado:
        - Botão esquerdo: move objeto, seleciona, ou pan (se vazio)
        - Botão direito: seleção retangular
        - Arrasta conexões quando clica nelas
        - Seleciona texto quando clica na caixa de texto
        """
        # Limpar seleção de texto em todos os itens quando clica fora
        item_clicked = self.itemAt(event.position().toPoint())
        
        # Se clicou em um QGraphicsProxyWidget (controles de mídia), deixa passar o evento
        from PySide6.QtWidgets import QGraphicsProxyWidget
        if isinstance(item_clicked, QGraphicsProxyWidget):
            super().mousePressEvent(event)
            return
        
        if not isinstance(item_clicked, (StyledNode, Handle)):
            # Clicou fora de qualquer item útil
            # Limpar seleção de texto
            for item in self.scene().items():
                if isinstance(item, StyledNode):
                    cursor = item.text.textCursor()
                    if cursor.hasSelection():
                        cursor.clearSelection()
                        item.text.setTextCursor(cursor)
            # Reexibir objetos ocultos ao clicar em espaço vazio
            main_window = QApplication.activeWindow()
            if hasattr(main_window, 'reveal_all_items'):
                main_window.reveal_all_items()
        
        # Verificar se clicou em uma conexão para iniciar drag
        if isinstance(item_clicked, SmartConnection):
            self._start_drag_connection(item_clicked, event.position().toPoint())
            return
        
        # Se clicou em um Handle, sempre deixa o evento passar para o Handle processar
        if isinstance(item_clicked, Handle):
            super().mousePressEvent(event)
            return
        
        # BOTÃO DIREITO: Seleção retangular
        if event.button() == Qt.RightButton:
            # Inicia seleção retangular com o botão direito
            self.setDragMode(QGraphicsView.RubberBandDrag)
            super().mousePressEvent(event)
            return
        
        # BOTÃO ESQUERDO
        if event.button() == Qt.LeftButton:
            item_clicked = self.itemAt(event.position().toPoint())
            
            # Se clicou em um item
            if item_clicked:
                # Verificar se o item clicado é filho de um StyledNode (ex: texto)
                parent_node = item_clicked
                while parent_node and not isinstance(parent_node, StyledNode):
                    parent_node = parent_node.parentItem()
                
                # Se encontrou um nó pai, usar o pai como item principal
                if parent_node:
                    item_clicked = parent_node
                
                # Se Ctrl está pressionado, alternar seleção (adicionar/remover)
                if event.modifiers() & Qt.ControlModifier:
                    if item_clicked.isSelected():
                        item_clicked.setSelected(False)
                    else:
                        item_clicked.setSelected(True)
                else:
                    # Se não está selecionado, deseleciona outros
                    if not item_clicked.isSelected():
                        self.scene().clearSelection()
                        item_clicked.setSelected(True)
                
                # Registra a posição original para TODOS os itens selecionados
                self._item_positions.clear()
                for item in self.scene().selectedItems():
                    if hasattr(item, 'setPos'):
                        self._item_positions[item] = item.pos()
                
                # NÃO chama super().mousePressEvent para evitar que o item se mova 
                # apenas com o clique. O movimento será controlado manualmente no mouseMoveEvent.
                self._dragging_item = item_clicked
                self._drag_start_pos = self.mapToScene(event.position().toPoint())
                event.accept()
                return
            
            # Se não clicou em item e não há seleção: inicia pan
            if not self.scene().selectedItems():
                self._panning = True
                self._last_pos = event.position().toPoint()
                self.setCursor(Qt.ClosedHandCursor)
                return
            
            # Se há seleção mas clicou no vazio, deseleciona
            self.scene().clearSelection()
            event.accept()
            return
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Se está arrastando uma conexão
        if self._dragging_connection and self._dragged_connection:
            self._update_drag_connection(event.position().toPoint())
            return
        
        # Se está fazendo pan com movimento suave
        if self._panning:
            # Calcular delta com movimento mais responsivo
            current_pos = event.position().toPoint()
            delta = current_pos - self._last_pos
            
            # Fator adaptativo baseado na velocidade do movimento
            delta_length = (delta.x()**2 + delta.y()**2)**0.5
            smooth_factor = 1.0 + min(delta_length * 0.02, 1.5)  # Mais suave para rápido, mais preciso para lento
            smooth_delta = delta * smooth_factor
            
            self._last_pos = current_pos
            
            # Atualizar scrollbars de forma otimizada
            h_scroll = self.horizontalScrollBar()
            v_scroll = self.verticalScrollBar()
            
            h_scroll.setValue(h_scroll.value() - int(smooth_delta.x()))
            v_scroll.setValue(v_scroll.value() - int(smooth_delta.y()))
            self._extend_scroll_range_if_needed()
            return
        
        # Se está arrastando um item (não apenas clicou, mas realmente está movendo)
        # Mas NÃO move se o foco estiver em uma caixa de texto (permitir seleção de texto)
        if self._dragging_item and event.buttons() & Qt.LeftButton:
            # Verificar se há uma caixa de texto com foco
            focus_item = self.scene().focusItem()
            if isinstance(focus_item, QGraphicsTextItem):
                # Texto tem foco, não mover o objeto
                return
            
            current_pos = self.mapToScene(event.position().toPoint())
            
            # Verificar se o mouse se moveu o suficiente para considerar um drag
            if not self._is_dragging:
                distance = (current_pos - self._drag_start_pos).manhattanLength()
                if distance < 5:  # Threshold de 5 pixels para considerar drag
                    return
                self._is_dragging = True
            
            # Mover TODOS os itens selecionados
            delta = current_pos - self._drag_start_pos
            
            # Preparar mudança de geometria para todos os itens selecionados
            for item, original_pos in self._item_positions.items():
                if item.isSelected():
                    item.prepareGeometryChange()
            
            # Mover os itens - cada nó atualiza suas conexões via itemChange
            for item, original_pos in self._item_positions.items():
                if item.isSelected():
                    new_pos = original_pos + delta
                    item.setPos(new_pos)
            
            # Forçar atualização da cena para redesenhar as conexões
            self.scene().update()
            
            # Mostrar linhas de alinhamento para o item sendo arrastado se estiver ativo
            main_window = QApplication.activeWindow()
            if hasattr(main_window, "alinhar_ativo") and main_window.alinhar_ativo:
                self.alignment_guides.show_guides(self._dragging_item)
            else:
                self.alignment_guides.clear_guides()
            return
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Limpar linhas de alinhamento
        self.alignment_guides.clear_guides()
        
        # Se estava arrastando uma conexão
        if self._dragging_connection and event.button() == Qt.LeftButton:
            self._end_drag_connection()
            return
        
        # Se estava fazendo seleção retangular (botão direito)
        if event.button() == Qt.RightButton and self.dragMode() == QGraphicsView.RubberBandDrag:
            # Resetar para modo de seleção padrão após seleção retangular
            self.setDragMode(QGraphicsView.NoDrag)
        
        # Se estava arrastando um item
        if self._dragging_item and event.button() == Qt.LeftButton:
            # Se não foi um drag real (apenas um clique), restaurar posições originais
            if not self._is_dragging:
                for item, original_pos in self._item_positions.items():
                    item.setPos(original_pos)
            else:
                # Rastrear movimento para undo/redo
                main_window = QApplication.activeWindow()
                if hasattr(main_window, 'undo_stack'):
                    for item, original_pos in self._item_positions.items():
                        if item.isSelected() and item.pos() != original_pos:
                            cmd = MoveItemCommand(item, original_pos, item.pos(), "Mover objeto")
                            main_window.undo_stack.push(cmd)
            
            # Resetar estado de drag
            self._dragging_item = None
            self._drag_start_pos = None
            self._is_dragging = False
            self._item_positions.clear()
        
        # Se estava fazendo pan
        if self._panning and event.button() == Qt.LeftButton:
            self._panning = False
        self.setCursor(Qt.ArrowCursor)

    def _start_drag_connection(self, connection, mouse_pos):
        """Inicia arrastar uma conexão"""
        self._dragging_connection = True
        self._dragged_connection = connection
        self._drag_offset = self.mapToScene(mouse_pos) - self.mapToScene(0, 0)
        
        # Destacar visualmente a conexão sendo arrastada
        pen = QPen(QColor("#ff6b35"), 5, Qt.SolidLine, Qt.RoundCap)
        connection.setPen(pen)
        connection.setZValue(1000)  # Trazer para frente
        
        self.setCursor(Qt.ClosedHandCursor)

    def _update_drag_connection(self, mouse_pos):
        """Atualiza posição da conexão sendo arrastada"""
        if not self._dragged_connection:
            return
        
        # Calcular nova posição na cena
        scene_pos = self.mapToScene(mouse_pos) - self._drag_offset
        
        # Para conexões, queremos ajustar visualmente, não mover o objeto real
        # Vamos criar um offset visual que dá impressão de arrastar
        source = self._dragged_connection.source
        target = self._dragged_connection.target
        
        if source and target:
            # Calcular centros
            sc = source.sceneBoundingRect().center()
            tc = target.sceneBoundingRect().center()
            
            # Adicionar offset para dar impressão de movimento
            offset_x = scene_pos.x() - (sc.x() + tc.x()) / 2
            offset_y = scene_pos.y() - (sc.y() + tc.y()) / 2
            
            # Limitar offset para não distorcer demais
            max_offset = 50
            offset_x = max(-max_offset, min(max_offset, offset_x))
            offset_y = max(-max_offset, min(max_offset, offset_y))
            
            # Forçar atualização do caminho com offset visual
            self._dragged_connection._visual_offset = QPointF(offset_x, offset_y)
            self._dragged_connection.update_path()

    def _end_drag_connection(self):
        """Finaliza arrastar uma conexão"""
        if not self._dragged_connection:
            return
        
        self._dragging_connection = False
        
        # Restaurar aparência normal
        pen = QPen(QColor("#0078d4"), 3, Qt.SolidLine, Qt.RoundCap)
        self._dragged_connection.setPen(pen)
        self._dragged_connection.setZValue(-1)  # Voltar para trás
        
        # Remover offset visual
        if hasattr(self._dragged_connection, '_visual_offset'):
            delattr(self._dragged_connection, '_visual_offset')
        
        self._dragged_connection.update_path()
        self._dragged_connection = None
        
        self.setCursor(Qt.ArrowCursor)


# ======================================================
# JANELA PRINCIPAL
# ======================================================
class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Amarelo Mind")
        self.setWindowIcon(IconManager.load_icon("Arquivos.png"))

        self.undo_stack = QUndoStack(self)
        self.current_file = None
        self.groups = []
        
        # Gerenciador de persistência
        self.persistence = PersistenceManager()
        
        # Autosave configuration
        self.autosave_enabled = False
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.setInterval(2000)  # Auto-save a cada 2 segundos
        self.autosave_timer.start()
        
        # Hide mode - controlled by button
        self.hide_mode_active = False
        self.hide_mode_hidden_items = []
        
        # Conectar sinais para detectar mudanças
        self.undo_stack.indexChanged.connect(self._on_undo_stack_changed)
        self._last_autosave_index = 0

        # Alinhar ativo por padrão
        self.alinhar_ativo = True
        
        # Tema atual
        self.current_theme_name = "Padrão"

        self.scene = QGraphicsScene(-100000, -100000, 200000, 200000)
        self.view = InfiniteCanvas(self.scene, self)
        self.view.set_undo_stack(self.undo_stack)
        self.setCentralWidget(self.view)
        
        # Filtro de itens
        self.item_filter = ItemFilter(self.scene)

        # Atalhos customizados
        self.custom_shortcuts = {
            "Novo": "Ctrl+N",
            "Abrir": "Ctrl+A",
            "Salvar": "Ctrl+S",
            "Exportar": "",
            "Desfazer": "Ctrl+Z",
            "Refazer": "Ctrl+R",
            "Copiar": "Ctrl+C",
            "Colar": "Ctrl+V",
            "Adicionar": "+",
            "Título": "",
            "Mídia": "",
            "Conectar": "C",
            "Ocultar": "Ctrl+O",
            "Excluir": "Delete",
            "Fonte": "",
            "Cores": "",
            "Alinhar": "D",
            "Temas": "",
            "Localizar": "Ctrl+F",
        }
        
        self.load_shortcuts_from_file()
        # Evita atalhos ambíguos (ex.: dois botões com a mesma tecla)
        self.sanitize_duplicate_shortcuts()
        
        self.load_styles()
        self.setup_toolbar()

        self.scene.selectionChanged.connect(self.update_button_states)
        self.scene.changed.connect(self.update_button_states)
        # Conecta sinais de seleção de texto em itens existentes
        self._connect_text_signals()
        self.update_button_states()

    def _connect_text_signals(self):
        """Conecta sinais de seleção de texto em todos os itens StyledNode"""
        for item in self.scene.items():
            if isinstance(item, StyledNode):
                if hasattr(item.text, 'selectionChanged'):
                    try:
                        item.text.selectionChanged.disconnect()
                    except:
                        pass  # Sinal não estava conectado
                    item.text.selectionChanged.connect(self.update_button_states)

    def _on_undo_stack_changed(self, index):
        """Detecta mudanças no undo/redo para acionar autosave"""
        if self.autosave_enabled and index != self._last_autosave_index:
            self._last_autosave_index = index
            # Resetar timer para evitar saves muito frequentes
            self.autosave_timer.stop()
            self.autosave_timer.start()
    
    def _autosave(self):
        """Executa autosave se houver mudanças e arquivo existir"""
        if self.current_file and self.undo_stack.canUndo():
            try:
                self.persistence.save_to_file(self.current_file, self.scene)
                self._update_window_title()  # Mostrar status de salvo
            except Exception as e:
                print(f"Erro no autosave: {e}")

    # --------------------------------------------------
    # STYLES
    # --------------------------------------------------
    def load_styles(self):
        self.load_theme_from_file()
        theme = THEMES.get(self.current_theme_name, THEMES["Padrão"])
        qss = generate_qss(theme)
        if qss:
            self.setStyleSheet(qss)
        canvas_bg = theme.get("canvas_bg", "#0f1621")
        self.view.setBackgroundBrush(QColor(canvas_bg))

    def _get_theme_file(self):
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "amarelo-mind")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "theme.json")

    def load_theme_from_file(self):
        theme_file = self._get_theme_file()
        if os.path.exists(theme_file):
            try:
                with open(theme_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.current_theme_name = saved.get("theme", "Padrão")
            except Exception:
                self.current_theme_name = "Padrão"

    def save_theme_to_file(self):
        theme_file = self._get_theme_file()
        try:
            with open(theme_file, "w", encoding="utf-8") as f:
                json.dump({"theme": self.current_theme_name}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Aviso: Não foi possível salvar tema: {e}")

    def apply_theme(self, theme_name):
        if theme_name not in THEMES:
            return
        self.current_theme_name = theme_name
        theme = THEMES[theme_name]
        qss = generate_qss(theme)
        if qss:
            self.setStyleSheet(qss)
        canvas_bg = theme.get("canvas_bg", "#0f1621")
        self.view.setBackgroundBrush(QColor(canvas_bg))
        self.save_theme_to_file()

    def show_themes_dialog(self):
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                                       QLabel, QButtonGroup, QRadioButton, QWidget)
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtGui import QPixmap, QPainter, QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Temas")
        dialog.setMinimumWidth(380)
        layout = QVBoxLayout(dialog)

        label = QLabel("Escolha o tema do aplicativo:")
        layout.addWidget(label)

        btn_group = QButtonGroup(dialog)
        theme_names = list(THEMES.keys())

        THEME_LABELS = {
            "Padrão": "Verde",
            "#661f41": "Vinho",
            "#11799e": "Azul-petróleo",
            "#dabbed": "Rosa",
        }

        for i, name in enumerate(theme_names):
            t = THEMES[name]
            row = QHBoxLayout()

            swatch = QLabel()
            swatch.setFixedSize(48, 48)
            pix = QPixmap(48, 48)
            pix.fill(Qt.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.Antialiasing)
            p.setBrush(QColor(t["primary"]))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(0, 0, 48, 48, 8, 8)
            p.setBrush(QColor(t["accent"]))
            p.drawRoundedRect(4, 32, 40, 12, 4, 4)
            p.end()
            swatch.setPixmap(pix)

            display_name = THEME_LABELS.get(name, name)
            rb = QRadioButton(display_name)
            if name == self.current_theme_name:
                rb.setChecked(True)
            rb.setStyleSheet("font-size: 14px;")

            row.addWidget(swatch)
            row.addWidget(rb)
            row.addStretch()
            layout.addLayout(row)
            btn_group.addButton(rb, i)

        theme = THEMES.get(self.current_theme_name, THEMES["Padrão"])
        preview = QPushButton()
        preview.setEnabled(False)
        preview.setFixedHeight(44)
        preview.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {theme['primary']}, stop:1 {theme['primary_dark']});"
            f"color: {theme['accent']}; border: 1px solid {theme['primary_light']};"
            f"border-radius: 10px; font-size: 13px; font-weight: 600;"
        )
        preview.setText(THEME_LABELS.get(self.current_theme_name, self.current_theme_name))
        layout.addWidget(preview)

        def on_theme_selected(idx):
            selected_name = theme_names[idx]
            t = THEMES[selected_name]
            lbl = THEME_LABELS.get(selected_name, selected_name)
            preview.setText(lbl)
            preview.setStyleSheet(
                f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {t['primary']}, stop:1 {t['primary_dark']});"
                f"color: {t['accent']}; border: 1px solid {t['primary_light']};"
                f"border-radius: 10px; font-size: 13px; font-weight: 600;"
            )

        btn_group.idClicked.connect(on_theme_selected)

        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Aplicar")
        cancel_btn = QPushButton("Fechar")

        def apply_selected():
            idx = btn_group.checkedId()
            if idx >= 0:
                self.apply_theme(theme_names[idx])
            dialog.accept()

        apply_btn.clicked.connect(apply_selected)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def _get_shortcuts_file(self):
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "amarelo-mind")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "shortcuts.json")

    def load_shortcuts_from_file(self):
        shortcuts_file = self._get_shortcuts_file()
        if os.path.exists(shortcuts_file):
            try:
                with open(shortcuts_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    for key, value in saved.items():
                        if key in self.custom_shortcuts:
                            self.custom_shortcuts[key] = value
            except Exception as e:
                print(f"Aviso: Não foi carregar atalhos: {e}")

    def save_shortcuts_to_file(self):
        shortcuts_file = self._get_shortcuts_file()
        try:
            with open(shortcuts_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_shortcuts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Aviso: Não foi salvar atalhos: {e}")

    def sanitize_duplicate_shortcuts(self):
        """Remove atalhos duplicados: quando dois botões usam a mesma combinação,
        o Qt marca o atalho como ambíguo ('Ambiguous shortcut overload') e
        NENHUM dos dois dispara. Mantém o primeiro botão da lista e limpa os demais."""
        seen = {}
        for name in list(self.custom_shortcuts.keys()):
            seq = (self.custom_shortcuts.get(name) or "").strip()
            self.custom_shortcuts[name] = seq
            if not seq:
                continue
            if seq in seen:
                print(f"Aviso: atalho '{seq}' já usado por '{seen[seq]}' - removido de '{name}'")
                self.custom_shortcuts[name] = ""
            else:
                seen[seq] = name

    # --------------------------------------------------
    # TOOLBAR
    # --------------------------------------------------
    def setup_toolbar(self):
        tb = QToolBar()
        tb.setIconSize(QSize(40, 40))
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        tb.setContextMenuPolicy(Qt.NoContextMenu)
        self.addToolBar(tb)

        def make_action(icon, tooltip, slot, shortcut_key=None):
            loaded_icon = IconManager.load_icon(icon, icon[0])
            print(f"DEBUG: Loading icon '{icon}' - valid={not loaded_icon.isNull()}")
            act = QAction(loaded_icon, "", self)
            act.setToolTip(tooltip)
            if shortcut_key is not None:
                # Sempre atribuir o atalho (mesmo vazio limpa o anterior),
                # para que atalhos salvos sejam aplicados JÁ na inicialização.
                act.setShortcut(self.custom_shortcuts.get(shortcut_key, ""))
            act.triggered.connect(slot)
            tb.addAction(act)
            return act

        self.act_new = make_action("Novo.png", "Novo mapa mental", self.new_window, "Novo")
        self.act_open = make_action("Abrir.png", "Abrir mapa mental", self.open_project, "Abrir")
        
        # Save button - autosave always on after file is created
        self.act_save = make_action("Salvar.png", "Salvar alterações", self.save_project, "Salvar")
        
        self.act_export = make_action("Exportar.png", "Exportar como imagem", self.export_png, "Exportar")

        tb.addSeparator()

        self.act_undo = self.undo_stack.createUndoAction(self, "")
        self.act_undo.setToolTip(f"Desfazer ({self.custom_shortcuts.get('Desfazer', 'Ctrl+Z')})")
        self.act_undo.setIcon(IconManager.load_icon("Desfazer.png", "↩"))
        self.act_undo.setShortcut(self.custom_shortcuts.get("Desfazer", "Ctrl+Z"))
        tb.addAction(self.act_undo)

        self.act_redo = self.undo_stack.createRedoAction(self, "")
        self.act_redo.setToolTip(f"Refazer ({self.custom_shortcuts.get('Refazer', 'Ctrl+R')})")
        self.act_redo.setIcon(IconManager.load_icon("Refazer.png", "↪"))
        self.act_redo.setShortcut(self.custom_shortcuts.get("Refazer", "Ctrl+R"))
        tb.addAction(self.act_redo)

        tb.addSeparator()

        self.act_copy = make_action("Copiar.png", "Copiar", self.copy_content, "Copiar")
        self.act_paste = make_action("Colar.png", "Colar", self.paste_content, "Colar")

        tb.addSeparator()

        self.act_add = make_action("Adicionar.png", "Adicionar objeto", self.add_object, "Adicionar")
        self.act_title = make_action("Titulo.png", "Marcar como título", self.toggle_title, "Título")
        self.act_media = make_action("Midia.png", "Mídia", self.insert_media, "Mídia")
        self.act_connect = make_action("Conectar.png", "Conectar ou desconectar", self.connect_nodes, "Conectar")
        
        # Botão ocultar/reexibir
        self.act_hide = make_action("Ocultar.png", "Ocultar ou reexibir objetos", self.toggle_hide_mode, "Ocultar")
        
        self.act_delete = make_action("Excluir.png", "Excluir", self.delete_selected, "Excluir")

        tb.addSeparator()

        self.act_font = make_action("Fonte.png", "Fonte", self.change_font, "Fonte")
        self.act_colors = make_action("Cores.png", "Cores", self.change_colors, "Cores")

        tb.addSeparator()

        self.act_align = make_action("Alinhar.png", "Alinhar objetos", self.align_objects, "Alinhar")
        self.act_themes = make_action("Temas.png", "Temas", self.show_themes_dialog, "Temas")

        tb.addSeparator()

        # Botão Localizar
        self.act_search = make_action("Localizar.png", "Localizar", self.show_search_dialog, "Localizar")

        # Botão Teclas de Atalho
        make_action("TecladeAtalho.png", "Teclas de atalho", self.show_shortcuts_dialog)

        # Botão Ajuda
        make_action("Ajuda.png", "Dicas de uso", self.show_help_dialog)

        # Botão Sobre
        make_action("Sobre.png", "Sobre o App", self.show_about_dialog)

    # --------------------------------------------------
    # HIDE MODE
    # --------------------------------------------------
    def toggle_hide_mode(self):
        """Alterna modo de ocultar/reexibir objetos"""
        if self.hide_mode_active:
            # Reexibir todos os objetos ocultos
            self.hide_mode_active = False
            for item in self.hide_mode_hidden_items:
                item.setVisible(True)
            self.hide_mode_hidden_items = []
            # Alternar ícone para Ocultar
            if hasattr(self, 'act_hide'):
                self.act_hide.setIcon(IconManager.load_icon("Ocultar.png", "O"))
        else:
            # Ocultar objetos não conectados ao selecionado
            sel = self.scene.selectedItems()
            styled_nodes = [item for item in sel if isinstance(item, StyledNode)]
            
            if len(styled_nodes) != 1:
                return
            
            selected_node = styled_nodes[0]
            self.hide_mode_active = True
            self.hide_mode_hidden_items = []
            
            # Encontrar nós conectados
            connected_nodes = {selected_node}
            connected_connections = set()
            
            for conn in self.scene.items():
                if isinstance(conn, SmartConnection):
                    if conn.source == selected_node:
                        connected_nodes.add(conn.target)
                        connected_connections.add(conn)
                    elif conn.target == selected_node:
                        connected_nodes.add(conn.source)
                        connected_connections.add(conn)
            
            # Ocultar nós não conectados
            for item in self.scene.items():
                if isinstance(item, (StyledNode, MediaItem)) and item not in connected_nodes:
                    if item.isVisible():
                        item.setVisible(False)
                        self.hide_mode_hidden_items.append(item)
            
            # Ocultar conexões não conectadas ao nó selecionado
            for conn in self.scene.items():
                if isinstance(conn, SmartConnection) and conn not in connected_connections:
                    if conn.isVisible():
                        conn.setVisible(False)
                        self.hide_mode_hidden_items.append(conn)
            
            # Alternar ícone para Reexibir
            if hasattr(self, 'act_hide'):
                self.act_hide.setIcon(IconManager.load_icon("Reexibir.png", "R"))
    
    def reveal_all_items(self):
        """Reexibe todos os objetos ocultos"""
        if self.hide_mode_active:
            self.hide_mode_active = False
            for item in self.hide_mode_hidden_items:
                item.setVisible(True)
            self.hide_mode_hidden_items = []
            if hasattr(self, 'act_hide'):
                self.act_hide.setIcon(IconManager.load_icon("Ocultar.png", "O"))
    
    # --------------------------------------------------
    # ESTADOS
    # --------------------------------------------------
    def update_button_states(self):
        try:
            sel = self.scene.selectedItems()
        except RuntimeError:
            return
        
        styled_nodes = [item for item in sel if isinstance(item, StyledNode)]
        
        # Habilitar/desabilitar botão ocultar
        if hasattr(self, 'act_hide'):
            self.act_hide.setEnabled(len(styled_nodes) == 1)
        
        # Botão Título: habilitado apenas com 1 nó selecionado
        if hasattr(self, 'act_title'):
            self.act_title.setEnabled(len(styled_nodes) == 1)
        
        has_sel = bool(self.scene.selectedItems())
        has_items = bool(self.scene.items())
        
        # Verificar se há um nó selecionado
        has_styled_node = any(isinstance(item, StyledNode) for item in sel)
        # Verificar se há mídia selecionada
        has_media_selected = any(isinstance(item, MediaItem) for item in sel)
        
        # Verificar se há foco em um texto dentro de um nó
        focus_item = self.scene.focusItem()
        is_text_in_node = isinstance(focus_item, QGraphicsTextItem) and isinstance(focus_item.parentItem(), StyledNode)
        
        # Botões Fonte e Cores habilitados se:
        # - Há um nó selecionado, OU
        # - Há foco em um texto dentro de um nó
        can_format = (has_styled_node or is_text_in_node) and not has_media_selected

        self.act_font.setEnabled(can_format)
        self.act_colors.setEnabled(can_format)
        self.act_export.setEnabled(has_items)

        # Botão Alinhar: habilitado se há 2+ objetos (StyledNode ou MediaItem)
        alignable = [i for i in sel if isinstance(i, (StyledNode, MediaItem))]
        self.act_align.setEnabled(len(alignable) >= 2)

        # Botão Copiar: habilitado se há texto com seleção
        # - Texto com seleção em foco, OU
        # - Nó selecionado (copia o texto do nó)
        can_copy = False
        if focus_item and isinstance(focus_item, QGraphicsTextItem):
            if focus_item.textCursor().hasSelection():
                can_copy = True
        if has_styled_node:
            can_copy = True
        self.act_copy.setEnabled(can_copy)

        # Botão Colar: habilitado se há texto no clipboard E (foco em texto OU nó selecionado)
        clipboard_text = QApplication.clipboard().text()
        can_paste = bool(clipboard_text) and (is_text_in_node or has_styled_node)
        self.act_paste.setEnabled(can_paste)

        # Botão Conectar: habilitado se há 1+ objeto selecionado (StyledNode ou MediaItem).
        # Com 1 objeto, abre o diálogo de desmembrar/conectar a outro mapa.
        # Com 2+, conecta os selecionados entre si.
        connectable_items = [i for i in sel if isinstance(i, (StyledNode, MediaItem))]
        self.act_connect.setEnabled(len(connectable_items) >= 1)

        # Botão Excluir: habilitado se há 1+ objeto selecionado
        self.act_delete.setEnabled(has_sel)

        # Botão Localizar: habilitado se há pelo menos um objeto com conteúdo textual
        can_search = False
        for item in self.scene.items():
            if isinstance(item, StyledNode):
                text = item.get_text()
                if text and text.strip():
                    can_search = True
                    break
            elif isinstance(item, MediaSliderImageItem):
                if hasattr(item, '_entries') and len(item._entries) > 0:
                    can_search = True
                    break
        self.act_search.setEnabled(can_search)

    def insert_media(self):
        sel = [i for i in self.scene.selectedItems() if isinstance(i, (MediaSliderImageItem, MediaAVSliderItem, MediaImageItem, MediaAVItem))]
        if sel:
            self._edit_media_playlist(sel[0])
            return
        
        choice = QMessageBox(self)
        choice.setWindowTitle("Inserir mídia")
        choice.setText("Escolha a origem da mídia")
        disco_btn = choice.addButton("Disco", QMessageBox.AcceptRole)
        url_btn = choice.addButton("URL", QMessageBox.ActionRole)
        cancel_btn = choice.addButton("Cancelar", QMessageBox.RejectRole)
        choice.exec()

        clicked = choice.clickedButton()
        if clicked == cancel_btn:
            return

        base_pos = self.view.mapToScene(self.view.viewport().rect().center())
        offset_x = 0

        if clicked == disco_btn:
            filters = (
                "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;"
                "Áudio (*.mp3 *.wav *.ogg);;"
                "Vídeo (*.mp4 *.avi *.mkv *.mov);;"
                "Todos (*.*)"
            )
            paths, _ = QFileDialog.getOpenFileNames(self, "Inserir mídia do disco", "", filters)
            if not paths:
                return
            images = []
            av_sources = []
            for p in paths:
                img = QImage(p)
                if not img.isNull():
                    images.append((img, p))
                else:
                    av_sources.append(p)
            if not images:
                if av_sources:
                    if len(av_sources) == 1:
                        item = MediaAVItem(av_sources[0])
                        item.setPos(base_pos)
                        self.undo_stack.push(AddItemCommand(self.scene, item, "Adicionar mídia AV", self))
                    else:
                        slider = MediaAVSliderItem(av_sources)
                        slider.setPos(base_pos)
                        self.undo_stack.push(AddItemCommand(self.scene, slider, "Adicionar slider AV", self))
                return
            if len(images) == 1:
                img, src = images[0]
                item = MediaImageItem(img, source=src)
                item.setPos(base_pos)
                self.undo_stack.push(AddItemCommand(self.scene, item, "Adicionar imagem", self))
            else:
                imgs = [im for im, _ in images]
                slider = MediaSliderImageItem(imgs, [s for _, s in images])
                slider.setPos(base_pos)
                self.undo_stack.push(AddItemCommand(self.scene, slider, "Adicionar slider de imagens", self))
            # Inserir também quaisquer arquivos AV restantes como itens individuais
            if av_sources:
                base_y = base_pos.y() + 20 + (images[0][0].height() if images else 0)
                if len(av_sources) == 1:
                    item = MediaAVItem(av_sources[0])
                    item.setPos(QPointF(base_pos.x(), base_y))
                    self.undo_stack.push(AddItemCommand(self.scene, item, "Adicionar mídia AV", self))
                else:
                    slider = MediaAVSliderItem(av_sources)
                    slider.setPos(QPointF(base_pos.x(), base_y))
                    self.undo_stack.push(AddItemCommand(self.scene, slider, "Adicionar slider AV", self))
            return

        if clicked == url_btn:
            text, ok = QInputDialog.getMultiLineText(self, "Inserir por URL", "Uma URL por linha:")
            if not ok or not text.strip():
                return
            urls = [u.strip() for u in text.splitlines() if u.strip()]
            img_pairs = []
            video_urls = []
            for u in urls:
                u_lower = u.lower()
                if any(ext in u_lower for ext in ['.mp4', '.avi', '.mkv', '.mov', '.mp3', '.wav', '.ogg', 'youtube.com', 'youtu.be', 'vimeo.com']):
                    video_urls.append(u)
                else:
                    try:
                        with urllib.request.urlopen(u) as resp:
                            data = resp.read()
                        img = QImage()
                        img.loadFromData(data)
                        if not img.isNull():
                            img_pairs.append((img, u))
                    except Exception:
                        pass
            
            if video_urls:
                if len(video_urls) == 1:
                    item = MediaAVItem(video_urls[0])
                    item.setPos(base_pos)
                    self.undo_stack.push(AddItemCommand(self.scene, item, "Adicionar vídeo", self))
                else:
                    slider = MediaAVSliderItem(video_urls)
                    slider.setPos(base_pos)
                    self.undo_stack.push(AddItemCommand(self.scene, slider, "Adicionar slider de vídeos", self))
                if not img_pairs:
                    return
            
            if not img_pairs:
                return
            if len(img_pairs) == 1:
                img, src = img_pairs[0]
                item = MediaImageItem(img, source=src)
                item.setPos(base_pos)
                self.undo_stack.push(AddItemCommand(self.scene, item, "Adicionar imagem", self))
            else:
                imgs = [im for im, _ in img_pairs]
                slider = MediaSliderImageItem(imgs, [s for _, s in img_pairs])
                slider.setPos(base_pos)
                self.undo_stack.push(AddItemCommand(self.scene, slider, "Adicionar slider de imagens", self))

    def _edit_media_playlist(self, media_item):
        if isinstance(media_item, MediaSliderImageItem):
            self._edit_image_slider_playlist(media_item)
        elif isinstance(media_item, MediaAVSliderItem):
            self._edit_av_slider_playlist(media_item)
        elif isinstance(media_item, MediaImageItem):
            self._edit_single_image(media_item)
        elif isinstance(media_item, MediaAVItem):
            self._edit_single_av(media_item)

    def _edit_single_image(self, media_item):
        """Edita uma imagem única - oferece converter para slider"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Imagem")
        dialog.setMinimumSize(400, 200)
        layout = QVBoxLayout(dialog)
        
        label = QLabel(f"Imagem: {media_item.source}")
        layout.addWidget(label)
        
        info = QLabel("Esta é uma imagem única. Deseja adicionar mais imagens para criar um slider?")
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Adicionar mais imagens")
        close_btn = QPushButton("Fechar")
        
        def add_more_images():
            filters = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Todos (*.*)"
            paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar imagens", "", filters)
            if not paths:
                return
            
            # Converter para slider
            images = []
            for p in paths:
                img = QImage(p)
                if not img.isNull():
                    images.append((img, p))
            
            if images:
                # Adicionar a imagem atual como primeira entrada
                current_pix = media_item._pix
                current_source = media_item.source
                
                all_images = [media_item._pix] + [img for img, _ in images]
                all_sources = [media_item.source] + [s for _, s in images]
                
                # Criar novo slider
                slider = MediaSliderImageItem(
                    [media_item._pix] + [img for img, _ in images],
                    [media_item.source] + [s for _, s in images]
                )
                slider.setPos(media_item.pos())
                
                # Substituir o item antigo pelo slider
                self.undo_stack.push(ReplaceMediaCommand(self.scene, media_item, slider, "Converter para slider"))
            
            dialog.accept()
        
        add_btn.clicked.connect(add_more_images)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        close_btn.clicked.connect(dialog.accept)
        dialog.exec()

    def _edit_single_av(self, media_item):
        """Edita um AV único - oferece converter para slider"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Vídeo/Áudio")
        dialog.setMinimumSize(400, 200)
        layout = QVBoxLayout(dialog)
        
        label = QLabel(f"Arquivo: {media_item.source}")
        layout.addWidget(label)
        
        info = QLabel("Este é um arquivo único. Deseja adicionar mais arquivos para criar uma playlist?")
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Adicionar mais arquivos")
        close_btn = QPushButton("Fechar")
        
        def add_more_files():
            filters = "Vídeo (*.mp4 *.avi *.mkv *.mov);;Áudio (*.mp3 *.wav *.ogg);;Todos (*.*)"
            paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar arquivos", "", filters)
            if not paths:
                return
            
            # Criar slider AV
            all_sources = [media_item.source] + paths
            slider = MediaAVSliderItem(all_sources)
            slider.setPos(media_item.pos())
            
            # Substituir o item antigo pelo slider
            self.undo_stack.push(ReplaceMediaCommand(self.scene, media_item, slider, "Converter para playlist"))
            
            dialog.accept()
        
        add_btn.clicked.connect(add_more_files)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        close_btn.clicked.connect(dialog.accept)
        dialog.exec()

    def _edit_image_slider_playlist(self, slider):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Playlist de Imagens")
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        if hasattr(slider, '_entries') and slider._entries:
            for entry in slider._entries:
                if hasattr(entry, 'get') and 'source' in entry:
                    list_widget.addItem(entry['source'])
                else:
                    list_widget.addItem(f"Imagem {list_widget.count() + 1}")
        layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Adicionar")
        remove_btn = QPushButton("Remover")
        up_btn = QPushButton("↑ Mover para Cima")
        down_btn = QPushButton("↓ Mover para Baixo")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        layout.addLayout(btn_layout)

        close_btn = QPushButton("Fechar")
        layout.addWidget(close_btn)

        def add_images():
            filters = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Todos (*.*)"
            paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar imagens", "", filters)
            if not paths:
                return
            for p in paths:
                img = QImage(p)
                if not img.isNull():
                    pix = QPixmap.fromImage(img)
                    slider._entries.append({"pix": pix, "source": p, "movie": None})
                    list_widget.addItem(p)
            slider._update_label()
            slider._rebuild_playlist_widget()
            slider.update()

        def remove_selected():
            row = list_widget.currentRow()
            if row >= 0 and row < len(slider._entries):
                slider._entries.pop(row)
                list_widget.takeItem(row)
                slider._update_label()
                slider._rebuild_playlist_widget()
                slider.update()

        def move_up():
            row = list_widget.currentRow()
            if row > 0:
                slider._entries[row], slider._entries[row-1] = slider._entries[row-1], slider._entries[row]
                item = list_widget.takeItem(row)
                list_widget.insertItem(row-1, item)
                list_widget.setCurrentRow(row-1)
                slider._rebuild_playlist_widget()
                slider.update()

        def move_down():
            row = list_widget.currentRow()
            if row >= 0 and row < len(slider._entries) - 1:
                slider._entries[row], slider._entries[row+1] = slider._entries[row+1], slider._entries[row]
                item = list_widget.takeItem(row)
                list_widget.insertItem(row+1, item)
                list_widget.setCurrentRow(row+1)
                slider._rebuild_playlist_widget()
                slider.update()

        add_btn.clicked.connect(add_images)
        remove_btn.clicked.connect(remove_selected)
        up_btn.clicked.connect(move_up)
        down_btn.clicked.connect(move_down)
        close_btn.clicked.connect(dialog.accept)

        dialog.exec()

    def _edit_av_slider_playlist(self, slider):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Playlist de Vídeos/Áudio")
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        if hasattr(slider, '_sources') and slider._sources:
            for src in slider._sources:
                list_widget.addItem(src)
        layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Adicionar")
        remove_btn = QPushButton("Remover")
        up_btn = QPushButton("↑ Mover para Cima")
        down_btn = QPushButton("↓ Mover para Baixo")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        layout.addLayout(btn_layout)

        close_btn = QPushButton("Fechar")
        layout.addWidget(close_btn)

        def add_videos():
            filters = "Vídeo (*.mp4 *.avi *.mkv *.mov);;Áudio (*.mp3 *.wav *.ogg);;Todos (*.*)"
            paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar vídeos/áudio", "", filters)
            if not paths:
                return
            for p in paths:
                slider._sources.append(p)
                list_widget.addItem(p)
            slider._load_current()

        def remove_selected():
            row = list_widget.currentRow()
            if row >= 0 and row < len(slider._sources):
                slider._sources.pop(row)
                list_widget.takeItem(row)
                slider._load_current()

        def move_up():
            row = list_widget.currentRow()
            if row > 0:
                slider._sources[row], slider._sources[row-1] = slider._sources[row-1], slider._sources[row]
                item = list_widget.takeItem(row)
                list_widget.insertItem(row-1, item)
                list_widget.setCurrentRow(row-1)
                slider._load_current()

        def move_down():
            row = list_widget.currentRow()
            if row >= 0 and row < len(slider._sources) - 1:
                slider._sources[row], slider._sources[row+1] = slider._sources[row+1], slider._sources[row]
                item = list_widget.takeItem(row)
                list_widget.insertItem(row+1, item)
                list_widget.setCurrentRow(row+1)
                slider._load_current()

        add_btn.clicked.connect(add_videos)
        remove_btn.clicked.connect(remove_selected)
        up_btn.clicked.connect(move_up)
        down_btn.clicked.connect(move_down)
        close_btn.clicked.connect(dialog.accept)

        dialog.exec()

    def _connect_text_signals(self):
        """Conecta sinais de seleção de texto de todos os StyledNode na cena"""
        for item in self.scene.items():
            if isinstance(item, StyledNode):
                if hasattr(item.text, 'selectionChanged'):
                    item.text.selectionChanged.connect(self.update_button_states)

    # --------------------------------------------------
    # FUNCIONALIDADES
    # --------------------------------------------------
    def new_window(self):
        """Abre uma nova janela completamente independente."""
        from PySide6.QtCore import QProcess
        QProcess.startDetached(sys.executable, [__file__])


    def set_node_style(self, style_type):
        """Define o estilo de cor para os nós selecionados"""
        sel = [item for item in self.scene.selectedItems() if isinstance(item, StyledNode)]
        if not sel:
            return

        self.undo_stack.beginMacro(f"Mudar estilo para {style_type}")
        for item in sel:
            old_state = {'node_type': item.node_type, 'custom_color': item.custom_color}
            new_state = {'node_type': style_type, 'custom_color': None}
            cmd = ChangeNodeStyleCommand(item, old_state, new_state)
            self.undo_stack.push(cmd)
        self.undo_stack.endMacro()
    
    def select_all_by_type(self, node_type: str):
        """Seleciona todos os nós de um tipo específico"""
        self.item_filter.select_by_type(node_type)
    
    def select_all_by_text(self, search_text: str):
        """Seleciona todos os nós que contêm um texto"""
        self.item_filter.select_by_text(search_text)
    
    def apply_style_to_filtered(self, style_type: str):
        """Aplica estilo a todos os itens filtrados"""
        items = [item for item in self.item_filter.get_filtered_items() if isinstance(item, StyledNode)]
        if items:
            cmd = ApplyStyleFilteredCommand(items, style_type, self.scene)
            self.undo_stack.push(cmd)

    def add_object(self):
        sel = self.scene.selectedItems()

        if len(sel) == 1 and isinstance(sel[0], (StyledNode, MediaItem)):
            source = sel[0]
            
            new_pos = find_best_position_radial(source, self.scene)
            
            node = StyledNode(new_pos.x(), new_pos.y())
            self.undo_stack.push(AddItemCommand(self.scene, node, "Adicionar objeto", self))
            connection = SmartConnection(source, node)
            self.undo_stack.push(AddItemCommand(self.scene, connection, "Conectar objeto", self))
            connection.update_path()
        else:
            pos = self.view.mapToScene(self.view.viewport().rect().center())
            node = StyledNode(pos.x(), pos.y())
            self.undo_stack.push(AddItemCommand(self.scene, node, "Adicionar objeto", self))

        self.scene.clearSelection()
        node.setSelected(True)
        node.text.setFocus(Qt.OtherFocusReason)

    def toggle_title(self):
        """Transforma o nó selecionado em título ou remove o título."""
        sel = [item for item in self.scene.selectedItems() if isinstance(item, StyledNode)]
        if len(sel) != 1:
            return
        node = sel[0]
        node.set_is_title(not node._is_title)
        self.scene.update()

    def delete_selected(self):
        to_remove = list(self.scene.selectedItems())
        seen_conn = set()
        
        for item in to_remove:
            if isinstance(item, SmartConnection):
                # Remover conexão diretamente se selecionada
                if item not in seen_conn:
                    seen_conn.add(item)
                    self.undo_stack.push(RemoveItemCommand(self.scene, item, "Remover conexão"))
            elif isinstance(item, (StyledNode, MediaItem)):
                # Remover conexões conectadas ao nó
                for conn in self.scene.items():
                    if isinstance(conn, SmartConnection) and conn not in seen_conn and (conn.source == item or conn.target == item):
                        seen_conn.add(conn)
                        self.undo_stack.push(RemoveItemCommand(self.scene, conn, "Remover conexão"))
                # Remover o nó ou mídia
                self.undo_stack.push(RemoveItemCommand(self.scene, item, "Remover objeto"))

    def connect_nodes(self):
        """Conecta ou desconecta objetos selecionados.

        Com exatamente 1 objeto selecionado, abre um diálogo com as opções:
        Desmembrar mapa mental, Conectar a outro mapa mental e Cancelar.
        Com 2+ objetos, conecta/desconecta os selecionados entre si.
        """
        sel = [i for i in self.scene.selectedItems() if isinstance(i, (StyledNode, MediaItem))]
        
        if len(sel) == 1:
            self._show_connect_dialog(sel[0])
            return
        
        if len(sel) < 2:
            return
        
        # Verificar se já existem conexões entre os objetos selecionados
        connections_to_remove = []
        
        for i in range(len(sel) - 1):
            source = sel[i]
            target = sel[i + 1]
            
            # Procurar por conexão existente entre source e target
            existing_connection = None
            for item in self.scene.items():
                if isinstance(item, SmartConnection):
                    if (item.source == source and item.target == target) or \
                       (item.source == target and item.target == source):
                        existing_connection = item
                        break
            
            if existing_connection:
                connections_to_remove.append(existing_connection)
            else:
                # Criar nova conexão
                connection = SmartConnection(source, target)
                self.undo_stack.push(AddItemCommand(self.scene, connection, "Conectar nós", self))
        
        # Remover conexões existentes (desconectar)
        for conn in connections_to_remove:
            self.undo_stack.push(RemoveItemCommand(self.scene, conn, "Desconectar nós"))

    # --------------------------------------------------
    # DIÁLOGO CONECTAR (1 OBJETO SELECIONADO)
    # --------------------------------------------------
    def _show_connect_dialog(self, obj):
        """Exibe o diálogo de conectividade para um único objeto selecionado."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Conectar ou desconectar")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("O que você deseja fazer?")
        btn_split = msg.addButton("Desmembrar mapa mental", QMessageBox.ButtonRole.AcceptRole)
        btn_merge = msg.addButton("Conectar a outro mapa mental", QMessageBox.ButtonRole.AcceptRole)
        btn_cancel = msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == btn_split:
            self._split_mindmap(obj)
        elif clicked == btn_merge:
            self._connect_to_other_mindmap(obj)
        # Cancelar: nada é feito

    def _get_posterior_subgraph(self, obj):
        """Retorna (descendants, conns_both, conns_boundary).

        descendants: objetos alcançados a partir de obj via source→target (recursivo).
        conns_both: conexões com ambas as pontas dentro de {obj} + descendants.
        conns_boundary: conexões que tocam o subgrafo mas só têm uma ponta nele.
        """
        descendants = set()
        stack = [obj]
        while stack:
            cur = stack.pop()
            for item in self.scene.items():
                if not isinstance(item, SmartConnection):
                    continue
                if item.source is cur and item.target not in descendants:
                    descendants.add(item.target)
                    stack.append(item.target)
        
        remove_set = {obj} | descendants
        conns_both = []
        conns_boundary = []
        for item in self.scene.items():
            if not isinstance(item, SmartConnection):
                continue
            in_src = item.source in remove_set
            in_tgt = item.target in remove_set
            if in_src and in_tgt:
                conns_both.append(item)
            elif in_src or in_tgt:
                conns_boundary.append(item)
        return descendants, conns_both, conns_boundary

    def _split_mindmap(self, obj):
        """Desmembra o mapa a partir do objeto selecionado.

        O objeto selecionado vira o TÍTULO de um novo mapa (nova janela),
        junto com toda a sua sub-árvore posterior (source→target). Os objetos
        que levavam até ele permanecem no mapa atual.
        """
        descendants, conns_both, conns_boundary = self._get_posterior_subgraph(obj)
        
        if not descendants:
            QMessageBox.information(
                self, "Desmembrar mapa mental",
                "O objeto selecionado não possui sub-mapa posterior.\nNenhuma alteração foi feita."
            )
            return
        
        remove_set = [obj] + sorted(descendants, key=id)
        
        # Criar a nova janela e transferir o subgrafo via comando undoável
        new_win = AmareloMainWindow()
        if not hasattr(self, "_opened_windows"):
            self._opened_windows = []
        self._opened_windows.append(new_win)
        cmd = SplitMapCommand(
            self.scene, new_win.scene, new_win,
            remove_set, conns_both, conns_boundary, obj
        )
        self.undo_stack.push(cmd)
        
        new_win._connect_text_signals()
        new_win.scene.clearSelection()
        obj.setSelected(True)
        new_win.update_button_states()
        new_win.show()
        new_win.view.centerOn(obj)
        
        self.update_button_states()
        # Alteração estrutural recente: garante persistência imediata
        if self.autosave_enabled and self.current_file:
            self._autosave()

    def _connect_to_other_mindmap(self, obj):
        """Conecta o objeto selecionado ao título de outro arquivo de mapa mental."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo", "", "Amarelo Mind (*.amind);;JSON (*.json)"
        )
        if not path:
            return
        
        # Ler apenas os dados para descobrir os títulos
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível ler o arquivo:\n{e}")
            return
        
        title_nodes = [n for n in data.get("nodes", []) if n.get("is_title")]
        if not title_nodes:
            QMessageBox.warning(
                self, "Erro",
                "O arquivo selecionado não possui nenhum objeto Título."
            )
            return
        
        chosen_title_data = title_nodes[0]
        if len(title_nodes) > 1:
            options = []
            for i, n in enumerate(title_nodes):
                text = (n.get("text") or "").strip()
                options.append(text if text else f"Título {i + 1}")
            choice, ok = QInputDialog.getItem(
                self, "Conectar a outro mapa mental",
                "O arquivo possui mais de um título.\nA qual título o objeto selecionado deve se conectar?",
                options, 0, False
            )
            if not ok:
                return
            idx = options.index(choice) if choice in options else 0
            chosen_title_data = title_nodes[idx]
        
        # Posicionar o mapa importado à direita do objeto selecionado
        anchor = QPointF(
            obj.sceneBoundingRect().right() + 80,
            obj.sceneBoundingRect().top()
        )
        nodes_map, connections = self.persistence.import_from_file(path, offset=anchor)
        if nodes_map is None:
            QMessageBox.critical(self, "Erro", "Falha ao importar o arquivo selecionado.")
            return
        if not nodes_map:
            QMessageBox.warning(self, "Erro", "O arquivo selecionado não contém objetos para importar.")
            return
        
        title_node = nodes_map.get(chosen_title_data.get("id"))
        
        self.undo_stack.beginMacro("Conectar a outro mapa mental")
        for node in nodes_map.values():
            self.undo_stack.push(AddItemCommand(self.scene, node, "Conectar a outro mapa mental", self))
        for conn in connections:
            self.undo_stack.push(AddItemCommand(self.scene, conn, "Conectar a outro mapa mental", self))
        if title_node is not None:
            connection = SmartConnection(obj, title_node)
            self.undo_stack.push(AddItemCommand(self.scene, connection, "Conectar a outro mapa mental", self))
        self.undo_stack.endMacro()
        
        self._connect_text_signals()
        self.scene.clearSelection()
        if title_node is not None:
            title_node.setSelected(True)
        self.update_button_states()

    def copy_content(self):
        # 1. Tenta copiar de item de texto em foco
        focus_item = self.scene.focusItem()
        if isinstance(focus_item, QGraphicsTextItem) and focus_item.textCursor().hasSelection():
            QApplication.clipboard().setText(focus_item.textCursor().selectedText())
            return

        # 2. Copia texto do nó selecionado
        sel = [i for i in self.scene.selectedItems() if isinstance(i, StyledNode)]
        if not sel:
            return
        node = sel[0]
        # Se o texto do nó tiver seleção, usa ela (caso o foco não esteja lá por algum motivo)
        cursor = node.text.textCursor()
        if cursor.hasSelection():
            QApplication.clipboard().setText(cursor.selectedText())
        else:
            QApplication.clipboard().setText(node.get_text())

    def paste_content(self):
        text = QApplication.clipboard().text()
        if not text:
            return

        # 1. Tenta colar em item de texto em foco
        focus_item = self.scene.focusItem()
        if isinstance(focus_item, QGraphicsTextItem):
            parent = focus_item.parentItem()
            if isinstance(parent, StyledNode):
                old_html = parent.text.toHtml()
                cursor = focus_item.textCursor()
                # Limpar formato antes de colar para evitar realce branco
                cursor.setCharFormat(QTextCharFormat())
                cursor.insertText(text)
                focus_item.setTextCursor(cursor)
                new_html = parent.text.toHtml()
                self.undo_stack.push(PasteTextCommand(parent, old_html, new_html, "Colar texto"))
                self.update_button_states()
                return

        # 2. Cola no nó selecionado
        sel = [i for i in self.scene.selectedItems() if isinstance(i, StyledNode)]
        if not sel:
            return
        node = sel[0]
        old_html = node.text.toHtml()
        cursor = node.text.textCursor()
        # Limpar formato antes de colar para evitar realce branco
        cursor.setCharFormat(QTextCharFormat())
        cursor.insertText(text)
        node.text.setTextCursor(cursor)
        new_html = node.text.toHtml()
        self.undo_stack.push(PasteTextCommand(node, old_html, new_html, "Colar texto"))
        self.update_button_states()

    def change_font(self):
        # Determinar o nó alvo
        target_node = None
        
        # 1. Tentar pegar nó do item com foco (texto sendo editado)
        focus_item = self.scene.focusItem()
        if isinstance(focus_item, QGraphicsTextItem):
            parent = focus_item.parentItem()
            if isinstance(parent, StyledNode):
                target_node = parent
        
        # 2. Se não tem foco, usar o primeiro nó selecionado
        if not target_node:
            for item in self.scene.selectedItems():
                if isinstance(item, StyledNode):
                    target_node = item
                    break
        
        if not target_node:
            return

        # Verificar se há seleção de texto
        cursor = target_node.text.textCursor()
        has_text_selection = cursor.hasSelection()
        
        # Passar a fonte e o formato do cursor para o diálogo
        current_font = target_node.text.font()
        cursor_format = None
        if has_text_selection:
            cursor_format = cursor.charFormat()
        
        # Abrir diálogo customizado
        font, fmt, ok = FontStyleDialog.get_font_and_format(current_font, self, cursor_format)
        
        if not ok:
            return
        
        old_html = target_node.text.document().toHtml()
        
        if has_text_selection:
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()
            cursor.setPosition(selection_start)
            cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
            
            cursor.mergeCharFormat(fmt)
            target_node.text.setTextCursor(cursor)
        else:
            target_node.text.setFont(font)
            cursor.select(cursor.SelectionType.Document)
            cursor.mergeCharFormat(fmt)
            target_node.text.setTextCursor(cursor)
        
        new_html = target_node.text.document().toHtml()
        
        if old_html != new_html:
            self.undo_stack.beginMacro("Mudar fonte")
            cmd = ChangeTextHtmlCommand(target_node, old_html, new_html, "Mudar fonte")
            self.undo_stack.push(cmd)
            self.undo_stack.endMacro()

    def change_colors(self):
        target_node = None
        target_connection = None

        for item in self.scene.selectedItems():
            if isinstance(item, SmartConnection):
                target_connection = item
                break

        if not target_connection:
            focus_item = self.scene.focusItem()
            if isinstance(focus_item, QGraphicsTextItem):
                parent = focus_item.parentItem()
                if isinstance(parent, StyledNode):
                    target_node = parent

            if not target_node:
                for item in self.scene.selectedItems():
                    if isinstance(item, StyledNode):
                        target_node = item
                        break

        if not target_node and not target_connection:
            return

        from core.dialogs import ColorPickerDialog

        if target_connection:
            current_color = target_connection.pen().color()
            color, ok = ColorPickerDialog.get_color_value(current_color, self)
            if ok:
                pen = target_connection.pen()
                pen.setColor(color)
                target_connection.setPen(pen)
                target_connection.update()
            return

        cursor = target_node.text.textCursor()
        has_text_selection = cursor.hasSelection()

        if has_text_selection:
            color, ok = ColorPickerDialog.get_color_value(QColor("#000000"), self)
            if not ok:
                return

            self.undo_stack.beginMacro("Mudar cor do texto")
            old_html = target_node.text.document().toHtml()
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            target_node.text.setTextCursor(cursor)
            new_html = target_node.text.document().toHtml()
            cmd = ChangeTextHtmlCommand(target_node, old_html, new_html, "Mudar cor do texto")
            self.undo_stack.push(cmd)
            self.undo_stack.endMacro()
        else:
            initial_color = QColor(target_node.custom_color) if target_node.custom_color else QColor("#FFFFFF")
            color, ok = ColorPickerDialog.get_color_value(initial_color, self)
            if ok:
                self.undo_stack.beginMacro("Mudar cor de fundo")
                old_state = {'node_type': target_node.node_type, 'custom_color': target_node.custom_color}
                new_state = {'node_type': target_node.node_type, 'custom_color': color.name()}
                cmd = ChangeNodeStyleCommand(target_node, old_state, new_state)
                self.undo_stack.push(cmd)
                self.undo_stack.endMacro()
    
    def toggle_shadow(self):
        items = [item for item in self.scene.selectedItems() if isinstance(item, StyledNode)]
        if items:
            cmd = ToggleShadowCommand(items)
            self.undo_stack.push(cmd)

    # --------------------------------------------------
    # ALINHAR OBJETOS
    # --------------------------------------------------
    def align_objects(self):
        """Alinha e distribui objetos selecionados conforme seus eixos."""
        sel = [item for item in self.scene.selectedItems()
               if isinstance(item, (StyledNode, MediaItem))]
        if len(sel) < 2:
            return

        rects = []
        for item in sel:
            br = item.boundingRect()
            pos = item.pos()
            rects.append((pos.x(), pos.y(), br.width(), br.height()))

        top_ys = [r[1] for r in rects]
        left_xs = [r[0] for r in rects]
        avg_top = sum(top_ys) / len(top_ys)
        avg_left = sum(left_xs) / len(left_xs)
        threshold = 30.0

        same_horizontal = all(abs(y - avg_top) < threshold for y in top_ys)
        same_vertical = all(abs(x - avg_left) < threshold for x in left_xs)

        old_positions = {item: item.pos() for item in sel}

        if same_horizontal and not same_vertical:
            top_y = min(r[1] for r in rects)
            sorted_items = sorted(zip(sel, rects), key=lambda t: t[1][0])
            total_width = sum(r[2] for _, r in sorted_items)
            gaps = len(sorted_items) - 1
            spacing = total_width / gaps if gaps > 0 else 0
            current_x = sorted_items[0][1][0]
            for item, rect in sorted_items:
                item.prepareGeometryChange()
                item.setPos(QPointF(current_x, top_y))
                current_x += rect[2] + spacing

        elif same_vertical and not same_horizontal:
            left_x = min(r[0] for r in rects)
            sorted_items = sorted(zip(sel, rects), key=lambda t: t[1][1])
            total_height = sum(r[3] for _, r in sorted_items)
            gaps = len(sorted_items) - 1
            spacing = total_height / gaps if gaps > 0 else 0
            current_y = sorted_items[0][1][1]
            for item, rect in sorted_items:
                item.prepareGeometryChange()
                item.setPos(QPointF(left_x, current_y))
                current_y += rect[3] + spacing

        elif same_horizontal and same_vertical:
            top_y = min(r[1] for r in rects)
            left_x = min(r[0] for r in rects)
            for item in sel:
                item.prepareGeometryChange()
                item.setPos(QPointF(left_x, top_y))

        else:
            top_y = min(r[1] for r in rects)
            sorted_items_h = sorted(zip(sel, rects), key=lambda t: t[1][0])
            total_width = sum(r[2] for _, r in sorted_items_h)
            gaps = len(sorted_items_h) - 1
            spacing = total_width / gaps if gaps > 0 else 0
            current_x = sorted_items_h[0][1][0]
            for item, rect in sorted_items_h:
                item.prepareGeometryChange()
                item.setPos(QPointF(current_x, top_y))
                current_x += rect[2] + spacing

        self.scene.update()
        for item in sel:
            if item in old_positions and item.pos() != old_positions[item]:
                self.undo_stack.push(MoveItemCommand(item, old_positions[item], item.pos(), "Alinhar objetos"))

    def _update_window_title(self):
        """Atualiza a barra de título: nome.amind - Amarelo Mind ou Amarelo Mind"""
        if self.current_file:
            name = os.path.basename(self.current_file)
            self.setWindowTitle(f"{name} - Amarelo Mind")
        else:
            self.setWindowTitle("Amarelo Mind")

    def save_project(self):
        """Salva o projeto em JSON"""
        if not self.scene.items():
            QMessageBox.warning(self, "Atenção", "Não há objetos para salvar.")
            return

        path = self.current_file
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Projeto", "", "Amarelo Mind (*.amind);;JSON (*.json)"
            )
            if not path:
                return
            if not path.endswith(".amind") and not path.endswith(".json"):
                path += ".amind"
            self.current_file = path

        if self.persistence.save_to_file(path, self.scene):
            self.current_file = path
            self.autosave_enabled = True  # Habilitar autosave após primeiro salvamento
            self._update_window_title()
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar o projeto.")

    def load_file(self, path):
        """Carrega um arquivo passedo como argumento"""
        if not path or not os.path.exists(path):
            return False
        
        self.current_file = path
        self.autosave_enabled = True
        self._last_autosave_index = self.undo_stack.index()
        
        if self.persistence.load_from_file(path, self.scene, self):
            self._update_window_title()
            self._update_custom_colors_from_scene()
            return True
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar o projeto: {os.path.basename(path)}")
            return False
    
    def _update_custom_colors_from_scene(self):
        """Extrai cores personalizadas dos nós e adiciona ao QColorDialog"""
        from PySide6.QtWidgets import QColorDialog
        custom_colors = set()
        for item in self.scene.items():
            if isinstance(item, StyledNode) and item.custom_color:
                custom_colors.add(item.custom_color)
        for i, color_hex in enumerate(sorted(custom_colors)):
            if i >= 16:
                break
            color = QColor(color_hex)
            QColorDialog.setCustomColor(i, color)

    def open_project(self):
        """Abre um ou mais projetos salvos"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Abrir Projeto(s)", "", "Amarelo Mind (*.amind);;JSON (*.json)"
        )
        if not paths:
            return

        for i, path in enumerate(paths):
            if i == 0:
                # Carrega o primeiro arquivo na janela atual
                self.current_file = path
                self.autosave_enabled = True  # Habilitar autosave para arquivo carregado
                self._last_autosave_index = self.undo_stack.index()  # Resetar index
                if self.persistence.load_from_file(path, self.scene, self):
                    self._update_window_title()
                else:
                    QMessageBox.critical(self, "Erro", f"Falha ao carregar o projeto: {os.path.basename(path)}")
            else:
                # Abre os arquivos subsequentes em novas janelas
                new_win = AmareloMainWindow()
                new_win.current_file = path
                if new_win.persistence.load_from_file(path, new_win.scene, new_win):
                    new_win._update_window_title()
                    new_win.show()
                else:
                    QMessageBox.critical(new_win, "Erro", f"Falha ao carregar o projeto: {os.path.basename(path)}")


    def export_png(self):
        if not self.scene.items():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar PNG", "", "PNG (*.png)"
        )
        if not path:
            return

        rect = self.scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
        w, h = max(1, int(rect.width())), max(1, int(rect.height()))

        image = QImage(w, h, QImage.Format_ARGB32)
        image.fill(QColor("#0f1621"))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        self.scene.render(
            painter,
            QRectF(0, 0, w, h),
            rect,
            Qt.IgnoreAspectRatio
        )
        painter.end()

        if not path.lower().endswith(".png"):
            path += ".png"
        image.save(path)

    def show_search_dialog(self):
        """Abre diálogo de pesquisa e busca no arquivo atual"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem
        from PySide6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Procurar")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Campo de pesquisa
        search_label = QLabel("Digite o texto para procurar:")
        layout.addWidget(search_label)
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Procurar...")
        layout.addWidget(search_input)
        
        # Botão procurar
        search_btn = QPushButton("Procurar")
        layout.addWidget(search_btn)
        
        # Lista de resultados
        results_label = QLabel("Resultados:")
        layout.addWidget(results_label)
        
        results_list = QListWidget()
        layout.addWidget(results_list)
        
        # Contador de resultados
        counter_label = QLabel("0 de 0 resultados")
        layout.addWidget(counter_label)
        
        # Botões de navegação
        nav_layout = QHBoxLayout()
        prev_btn = QPushButton("◀ Anterior")
        prev_btn.setEnabled(False)
        nav_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Próximo ▶")
        next_btn.setEnabled(False)
        nav_layout.addWidget(next_btn)
        
        layout.addLayout(nav_layout)
        
        dialog.setLayout(layout)
        
        # Variáveis para controle
        search_results = []
        current_index = -1
        
        # Função de busca
        def do_search():
            nonlocal search_results, current_index
            results_list.clear()
            search_results.clear()
            current_index = -1
            
            search_text = search_input.text().lower()
            
            if not search_text:
                counter_label.setText("0 de 0 resultados")
                prev_btn.setEnabled(False)
                next_btn.setEnabled(False)
                return
            
            # Buscar em todos os nós
            for item in self.scene.items():
                if isinstance(item, StyledNode):
                    text = item.get_text().lower()
                    if search_text in text:
                        # Criar item na lista com preview do texto
                        preview = item.get_text()[:50] + "..." if len(item.get_text()) > 50 else item.get_text()
                        list_item = QListWidgetItem(preview)
                        list_item.setData(Qt.UserRole, item)  # Guardar referência ao objeto
                        results_list.addItem(list_item)
                        search_results.append(item)
            
            # Atualizar contador
            total = len(search_results)
            if total > 0:
                counter_label.setText(f"1 de {total} resultados")
                current_index = 0
                results_list.setCurrentRow(0)
                go_to_result(0)
                prev_btn.setEnabled(total > 1)
                next_btn.setEnabled(total > 1)
            else:
                results_list.addItem("Nenhum resultado encontrado")
                counter_label.setText("0 de 0 resultados")
                prev_btn.setEnabled(False)
                next_btn.setEnabled(False)
        
        # Função para ir para um resultado específico
        def go_to_result(index):
            nonlocal current_index
            if 0 <= index < len(search_results):
                current_index = index
                item = search_results[index]
                
                # Desselecionar todos os itens primeiro
                self.scene.clearSelection()
                
                # Ajustar zoom para focar no item (zoom 100%)
                self.view.resetTransform()
                self.view.scale(1.0, 1.0)
                
                # Centralizar na visualização
                self.view.centerOn(item)
                
                # Selecionar o item e garantir que está visível
                item.setSelected(True)
                
                # Garantir que o item está na frente
                item.setZValue(1000)
                
                # Agendar para restaurar z-value após um tempo
                def restore_z():
                    if item:
                        item.setZValue(0)
                QTimer.singleShot(2000, restore_z)
                
                # Atualizar lista
                results_list.setCurrentRow(index)
                
                # Atualizar contador
                counter_label.setText(f"{index + 1} de {len(search_results)} resultados")
                
                # Atualizar botões
                prev_btn.setEnabled(index > 0)
                next_btn.setEnabled(index < len(search_results) - 1)
        
        # Navegação anterior
        def go_previous():
            nonlocal current_index
            if current_index > 0:
                go_to_result(current_index - 1)
        
        # Navegação próximo
        def go_next():
            nonlocal current_index
            if current_index < len(search_results) - 1:
                go_to_result(current_index + 1)
        
        # Conectar sinais
        search_btn.clicked.connect(do_search)
        search_input.returnPressed.connect(do_search)
        prev_btn.clicked.connect(go_previous)
        next_btn.clicked.connect(go_next)
        results_list.itemClicked.connect(lambda item: go_to_result(results_list.row(item)))
        
        # Focar no campo de pesquisa
        search_input.setFocus()
        
        dialog.exec()


    def show_shortcuts_dialog(self):
        """Abre diálogo para visualizar e editar teclas de atalho"""
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                                       QTableWidgetItem, QPushButton, QLabel, QHeaderView, 
                                       QMessageBox, QLineEdit)
        from PySide6.QtCore import Qt, QEvent, QObject
        
        all_buttons = [
            "Novo", "Abrir", "Salvar", "Exportar",
            "Desfazer", "Refazer",
            "Copiar", "Colar",
            "Adicionar", "Título", "Mídia", "Conectar", "Ocultar", "Excluir",
            "Fonte", "Cores",
            "Alinhar", "Temas",
            "Localizar"
        ]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Teclas de Atalho")
        dialog.setMinimumSize(500, 450)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Selecione uma linha e pressione a combinação de teclas desejada:")
        layout.addWidget(label)
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Botão", "Atalho"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.setRowCount(len(all_buttons))
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnWidth(1, 150)
        
        shortcut_edits = {}
        
        for i, name in enumerate(all_buttons):
            table.setItem(i, 0, QTableWidgetItem(name))
            
            shortcut_edit = QLineEdit()
            shortcut_edit.setReadOnly(True)
            shortcut_edit.setPlaceholderText("Pressione teclas...")
            shortcut_edit.setText(self.custom_shortcuts.get(name, ""))
            shortcut_edit.setMinimumWidth(140)
            shortcut_edit.setAlignment(Qt.AlignCenter)
            shortcut_edit.setMinimumHeight(40)
            shortcut_edits[name] = shortcut_edit
            table.setCellWidget(i, 1, shortcut_edit)
            table.setRowHeight(i, 48)
        
        table.resizeRowsToContents()
        layout.addWidget(table)
        
        info_label = QLabel("Dica: Pressione Escape para limpar. Selecione a linha e digite as teclas.")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)
        
        btn_layout = QHBoxLayout()
        
        class ShortcutFilter(QObject):
            def __init__(self, tbl, edits, btns):
                super().__init__()
                self.tbl = tbl
                self.edits = edits
                self.btns = btns
            
            def eventFilter(self, obj, event):
                if event.type() == QEvent.KeyPress:
                    row = self.tbl.currentRow()
                    if row < 0:
                        return False
                    
                    key = event.key()
                    modifiers = event.modifiers()
                    
                    if key == Qt.Key_Escape:
                        self.edits[self.btns[row]].setText("")
                        event.accept()
                        return True
                    
                    if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta,
                           Qt.Key_Tab, Qt.Key_Backtab):
                        return False
                    
                    combo = []
                    if modifiers & Qt.ControlModifier:
                        combo.append("Ctrl")
                    if modifiers & Qt.AltModifier:
                        combo.append("Alt")
                    if modifiers & Qt.ShiftModifier:
                        combo.append("Shift")
                    if modifiers & Qt.MetaModifier:
                        combo.append("Meta")
                    
                    key_name = ""
                    if key == Qt.Key_Space:
                        key_name = "Space"
                    elif key == Qt.Key_Return:
                        key_name = "Enter"
                    elif key == Qt.Key_Backspace:
                        key_name = "Backspace"
                    elif key == Qt.Key_Delete:
                        key_name = "Delete"
                    elif key == Qt.Key_Tab:
                        key_name = "Tab"
                    elif Qt.Key_F1 <= key <= Qt.Key_F12:
                        key_name = f"F{key - Qt.Key_F1 + 1}"
                    elif key == Qt.Key_Left:
                        key_name = "Left"
                    elif key == Qt.Key_Right:
                        key_name = "Right"
                    elif key == Qt.Key_Up:
                        key_name = "Up"
                    elif key == Qt.Key_Down:
                        key_name = "Down"
                    else:
                        key_text = event.text()
                        if key_text and key_text.isprintable():
                            key_name = key_text.upper()
                    
                    if key_name:
                        combo.append(key_name)
                    
                    if combo:
                        self.edits[self.btns[row]].setText("+".join(combo))
                        event.accept()
                        return True
                    
                    return False
                return False
        
        shortcut_filter = ShortcutFilter(table, shortcut_edits, all_buttons)
        dialog.installEventFilter(shortcut_filter)
        table.installEventFilter(shortcut_filter)
        for edit in shortcut_edits.values():
            edit.installEventFilter(shortcut_filter)
        
        def apply_shortcuts():
            # Bloquear atalhos duplicados ANTES de salvar (Qt não dispara combinação ambígua)
            ocorrencias = {}
            for name, edit in shortcut_edits.items():
                seq = edit.text().strip()
                if not seq:
                    continue
                if seq in ocorrencias:
                    QMessageBox.warning(
                        dialog, "Atalho duplicado",
                        f"O atalho '{seq}' já está em uso por '{ocorrencias[seq]}'.\n"
                        "Limpe ou troque um dos dois antes de salvar."
                    )
                    return
                ocorrencias[seq] = name

            for name, edit in shortcut_edits.items():
                self.custom_shortcuts[name] = edit.text().strip()

            self.sanitize_duplicate_shortcuts()
            self.save_shortcuts_to_file()
            update_toolbar_shortcuts()
            QMessageBox.information(dialog, "Sucesso", "Atalhos salvos e atualizados!")
        
        def update_toolbar_shortcuts():
            self.act_new.setShortcut(self.custom_shortcuts.get("Novo", ""))
            self.act_new.setToolTip(f"Novo ({self.custom_shortcuts.get('Novo', '')})")
            
            self.act_open.setShortcut(self.custom_shortcuts.get("Abrir", ""))
            self.act_open.setToolTip(f"Abrir ({self.custom_shortcuts.get('Abrir', '')})")
            
            self.act_save.setShortcut(self.custom_shortcuts.get("Salvar", ""))
            self.act_save.setToolTip(f"Salvar ({self.custom_shortcuts.get('Salvar', '')})")
            
            if hasattr(self, 'act_export'):
                self.act_export.setShortcut(self.custom_shortcuts.get("Exportar", ""))
            
            self.act_undo.setShortcut(self.custom_shortcuts.get("Desfazer", ""))
            self.act_undo.setToolTip(f"Desfazer ({self.custom_shortcuts.get('Desfazer', '')})")
            
            self.act_redo.setShortcut(self.custom_shortcuts.get("Refazer", ""))
            self.act_redo.setToolTip(f"Refazer ({self.custom_shortcuts.get('Refazer', '')})")
            
            self.act_copy.setShortcut(self.custom_shortcuts.get("Copiar", ""))
            self.act_paste.setShortcut(self.custom_shortcuts.get("Colar", ""))
            
            self.act_add.setShortcut(self.custom_shortcuts.get("Adicionar", ""))
            
            if hasattr(self, 'act_title'):
                self.act_title.setShortcut(self.custom_shortcuts.get("Título", ""))
            
            if hasattr(self, 'act_media'):
                self.act_media.setShortcut(self.custom_shortcuts.get("Mídia", ""))
            
            self.act_connect.setShortcut(self.custom_shortcuts.get("Conectar", ""))
            self.act_delete.setShortcut(self.custom_shortcuts.get("Excluir", ""))
            
            if hasattr(self, 'act_font'):
                self.act_font.setShortcut(self.custom_shortcuts.get("Fonte", ""))
            
            if hasattr(self, 'act_colors'):
                self.act_colors.setShortcut(self.custom_shortcuts.get("Cores", ""))
            
            if hasattr(self, 'act_align'):
                self.act_align.setShortcut(self.custom_shortcuts.get("Alinhar", ""))
            if hasattr(self, 'act_themes'):
                self.act_themes.setShortcut(self.custom_shortcuts.get("Temas", ""))
            
            self.act_search.setShortcut(self.custom_shortcuts.get("Localizar", ""))
            
            if hasattr(self, 'act_hide'):
                self.act_hide.setShortcut(self.custom_shortcuts.get("Ocultar", ""))
        
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(apply_shortcuts)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def show_help_dialog(self):
        """Abre diálogo de ajuda com dicas de uso"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
        from PySide6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Dicas de Uso")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        help_text = """
<h2>Bem-vindo ao Amarelo Mind!</h2>

<p>Aqui estão algumas dicas para ajudá-lo a usar o aplicativo:</p>

<h3>📝 Criando seu mapa mental</h3>
<ul>
<li>Clique no botão <b>Novo</b> para criar um novo mapa mental</li>
<li>Clique no botão <b>Adicionar</b> para adicionar novos nós</li>
<li>Clique duas vezes em um nó para editar o texto</li>
</ul>

<h3>🔗 Conectando nós</h3>
<ul>
<li>Selecione dois nós e clique em <b>Conectar</b> para criar uma conexão</li>
<li>As conexões são automáticas e se ajustam quando você move os nós</li>
</ul>

<h3>🎨 Personalizando</h3>
<ul>
<li>Use <b>Fonte</b> para alterar a fonte do texto</li>
<li>Use <b>Cores</b> para alterar as cores dos nós</li>
<li>Redimensione os nós usando as alças nos cantos</li>
</ul>

<h3>🖼️ Mídia</h3>
<ul>
<li>Insira imagens usando o botão <b>Mídia</b></li>
<li>Arraste e solte imagens diretamente na cena</li>
<li>Para múltiplas imagens, um slideshow será criado automaticamente</li>
</ul>

<h3>⌨️ Atalhos de teclado</h3>
<ul>
<li>Clique no botão <b>Teclas de atalho</b> para personalizar os atalhos</li>
<li>Os atalhos são salvos automaticamente</li>
</ul>

<h3>💾 Salvando e exportando</h3>
<ul>
<li>Use <b>Salvar</b> para salvar seu trabalho</li>
<li>Use <b>Exportar</b> para exportar como imagem PNG</li>
</ul>
"""
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel(help_text)
        content.setTextFormat(Qt.RichText)
        content.setWordWrap(True)
        content.setMargin(10)
        scroll.setWidget(content)
        
        layout.addWidget(scroll)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def show_about_dialog(self):
        """Abre diálogo sobre o aplicativo"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Sobre o App")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        about_text = """
<h2>Amarelo Mind</h2>

<p><b>Versão 1.6.5</b></p>

<p>Um aplicativo de mapa mental moderno e intuitivo.</p>

<p><b>Recursos:</b></p>
<ul>
<li>Crie e edite mapas mentais com facilidade</li>
<li>Adicione imagens</li>
<li>Conecte nós automaticamente</li>
<li>Personalize cores e fontes</li>
<li>Exporte seu trabalho como imagem</li>
<li>Atalhos de teclado personalizáveis</li>
</ul>

<p>© 2026 Amarelo Mind. Todos os direitos reservados.</p>

<p>Desenvolvido por: Roberto Araujo de Moraes Freitas</p>
"""
        
        label = QLabel(about_text)
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setMargin(20)
        
        layout.addWidget(label)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

    # --------------------------------------------------
    # QUIZ
    # --------------------------------------------------
    def show_quiz_dialog(self):
        """Abre o diálogo de quiz interativo"""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            QRadioButton, QButtonGroup, QWidget, QComboBox
        )
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        file_path = self.current_file if self.current_file else None
        has_content = self.quiz_manager.analyze_scene(self.scene, file_path)
        
        if not has_content:
            QMessageBox.information(
                self, "Quiz",
                "Crie conexões entre objetos no mapa mental para gerar perguntas de quiz."
            )
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Quiz - Perguntas sobre o Mapa")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        header = QLabel("Perguntas sobre seu Mapa Mental")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        consecutive_label = QLabel("Acertos consecutivos: 0")
        consecutive_label.setFont(QFont("Arial", 12))
        consecutive_label.setAlignment(Qt.AlignCenter)
        consecutive_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        layout.addWidget(consecutive_label)
        
        layout.addWidget(QLabel("<hr>"))
        
        question_label = QLabel("")
        question_label.setFont(QFont("Arial", 11))
        question_label.setWordWrap(True)
        layout.addWidget(question_label)
        
        button_group = QButtonGroup(dialog)
        option_widget = QWidget()
        option_layout = QVBoxLayout(option_widget)
        
        def load_question():
            q = self.quiz_manager.get_next_question()
            if not q:
                question_label.setText("Não há perguntas disponíveis.")
                return False
            
            question_label.setText(f"<b>Pergunta:</b> {q.question}")
            
            for i in option_layout.children():
                if isinstance(i, QWidget):
                    i.deleteLater()
            
            for alt in q.alternatives:
                rb = QRadioButton(alt)
                option_layout.addWidget(rb)
                button_group.addButton(rb)
            
            return True
        
        layout.addWidget(option_widget)
        
        feedback_label = QLabel("")
        feedback_label.setWordWrap(True)
        feedback_label.setStyleSheet("padding: 10px; border-radius: 5px;")
        layout.addWidget(feedback_label)
        
        correction_label = QLabel("")
        correction_label.setWordWrap(True)
        correction_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px;")
        correction_label.setVisible(False)
        layout.addWidget(correction_label)
        
        def submit_answer():
            selected = button_group.checkedButton()
            if not selected:
                return
            
            selected_text = selected.text()
            result = self.quiz_manager.answer_question(
                self.quiz_manager.state.questions[0].id if self.quiz_manager.state.questions else "",
                selected_text
            )
            
            consecutive = self.quiz_manager.get_consecutive_count()
            consecutive_label.setText(f"Acertos consecutivos: {consecutive}")
            
            if result.get("correct"):
                feedback_label.setText(f"✓ Correto! Muito bem!")
                feedback_label.setStyleSheet("color: green; padding: 10px; font-weight: bold;")
                consecutive_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                feedback_label.setText(f"✗ Errado. A resposta correta é: {result.get('correct_answer', 'N/A')}")
                feedback_label.setStyleSheet("color: red; padding: 10px; font-weight: bold;")
                consecutive_label.setStyleSheet("color: red; font-weight: bold;")
                
                correction_label.setText(
                    f"<b>Explicação:</b> {result.get('explanation', '')}"
                )
                correction_label.setVisible(True)
                
                current_q = self.quiz_manager.state.questions[0] if self.quiz_manager.state.questions else None
                if current_q:
                    correction_layout = QHBoxLayout()
                    correction_layout.addWidget(QLabel("Corrigir resposta:"))
                    correction_combo = QComboBox()
                    for alt in current_q.alternatives:
                        correction_combo.addItem(alt)
                    correction_combo.setCurrentText(result.get('correct_answer', ''))
                    correction_layout.addWidget(correction_combo)
                    
                    def save_correction():
                        new_answer = correction_combo.currentText()
                        self.quiz_manager.correct_answer(current_q.id, new_answer)
                        correction_label.setText(f"Resposta corrigida para: {new_answer}")
                    
                    correct_btn = QPushButton("Salvar Correção")
                    correct_btn.clicked.connect(save_correction)
                    correction_layout.addWidget(correct_btn)
                    correction_layout.addStretch()
                    correction_label.layout() if correction_label.layout() else None
            
            next_btn.setEnabled(True)
        
        def next_question():
            feedback_label.setText("")
            correction_label.setVisible(False)
            correction_label.setText("")
            next_btn.setEnabled(False)
            button_group.setExclusive(False)
            for btn in button_group.buttons():
                btn.setChecked(False)
                btn.setEnabled(True)
            button_group.setExclusive(True)
            load_question()
        
        next_btn = QPushButton("Próxima Pergunta")
        next_btn.setEnabled(False)
        next_btn.clicked.connect(next_question)
        layout.addWidget(next_btn)
        
        submit_btn = QPushButton("Responder")
        submit_btn.clicked.connect(submit_answer)
        layout.addWidget(submit_btn)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()


  # ======================================================
  # MAIN
  # ======================================================
  # MAIN
  # ======================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Estilo global e configuração
    app.setStyle("Fusion")
    
    app.setApplicationName("AmareloMind")
    app.setApplicationDisplayName("Amarelo Mind")
    
    # Registrar ícone para arquivos .amind (Windows only)
    try:
        from register_icon import register_icon
        register_icon()
    except Exception as e:
        print(f"Aviso: Não foi possível registrar ícone .amind: {e}")
    
    window = AmareloMainWindow()
    window.showMaximized()
    
    sys.exit(app.exec())
