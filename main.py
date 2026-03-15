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
    QTextCursor, QTextCharFormat, QPen, QPixmap
)

# ======================================================
# PATHS / ÍCONES
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from core.icon_manager import IconManager
from core.persistence import PersistenceManager
from core.item_filter import ItemFilter
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
        
        self.setBackgroundBrush(QColor("#f7d5a1"))
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
            
            for item, original_pos in self._item_positions.items():
                if item.isSelected():
                    new_pos = original_pos + delta
                    item.prepareGeometryChange()
                    item.setPos(new_pos)
            
            # Atualizar conexões para todos os itens movidos
            try:
                from core.connection import SmartConnection
                for item in self._item_positions.keys():
                    if item.isSelected() and item.scene():
                        for conn in item.scene().items():
                            if isinstance(conn, SmartConnection) and (conn.source == item or conn.target == item):
                                conn.update_path()
                                conn.update()
            except:
                pass
            
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
        self.setWindowIcon(IconManager.load_icon("App_icon.ico"))

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
            "Mídia": "",
            "Conectar": "C",
            "Excluir": "Delete",
            "Fonte": "",
            "Cores": "",
            "Localizar": "Ctrl+F",
            "Ocultar": "Ctrl+O",
        }
        
        self.load_shortcuts_from_file()
        
        self.load_styles()
        self.setup_toolbar()

        self.scene.selectionChanged.connect(self.update_button_states)
        self.scene.changed.connect(self.update_button_states)
        # Conecta sinais de seleção de texto em itens existentes
        self._connect_text_signals()
        self.update_button_states()

        self.showMaximized()

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
        qss = os.path.join(BASE_DIR, "styles.qss")
        if os.path.exists(qss):
            with open(qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _get_shortcuts_file(self):
        return os.path.join(BASE_DIR, "shortcuts.json")

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
            act = QAction(IconManager.load_icon(icon, icon[0]), "", self)
            act.setToolTip(tooltip)
            act.setContextMenuPolicy(Qt.NoContextMenu)
            shortcut = self.custom_shortcuts.get(shortcut_key) if shortcut_key else None
            if shortcut:
                act.setShortcut(shortcut)
            act.triggered.connect(slot)
            tb.addAction(act)
            return act

        self.act_new = make_action("Novo.png", "Novo mapa mental", self.new_window, "Novo")
        self.act_open = make_action("Abrir.png", "Abrir mapa mental", self.open_project, "Abrir")
        
        # Save button - autosave always on after file is created
        self.act_save = make_action("Salvar.png", "Salvar alterações", self.save_project, "Salvar")
        
        self.act_export = make_action("Exportar.png", "Exportar como imagem", self.export_png)

        tb.addSeparator()

        self.act_undo = self.undo_stack.createUndoAction(self, "")
        self.act_undo.setToolTip(f"Desfazer ({self.custom_shortcuts.get('Desfazer', 'Ctrl+Z')})")
        self.act_undo.setIcon(IconManager.load_icon("Desfazer.png", "D"))
        self.act_undo.setShortcut(self.custom_shortcuts.get("Desfazer", "Ctrl+Z"))
        self.act_undo.setContextMenuPolicy(Qt.NoContextMenu)
        tb.addAction(self.act_undo)

        self.act_redo = self.undo_stack.createRedoAction(self, "")
        self.act_redo.setToolTip(f"Refazer ({self.custom_shortcuts.get('Refazer', 'Ctrl+R')})")
        self.act_redo.setIcon(IconManager.load_icon("Refazer.png", "R"))
        self.act_redo.setShortcut(self.custom_shortcuts.get("Refazer", "Ctrl+R"))
        self.act_redo.setContextMenuPolicy(Qt.NoContextMenu)
        tb.addAction(self.act_redo)

        tb.addSeparator()

        self.act_copy = make_action("Copiar.png", "Copiar", self.copy_content, "Copiar")
        self.act_paste = make_action("Colar.png", "Colar", self.paste_content, "Colar")

        tb.addSeparator()

        self.act_add = make_action("Adicionar.png", "Adicionar objeto", self.add_object, "Adicionar")
        self.act_media = make_action("Midia.png", "Mídia", self.insert_media)
        self.act_connect = make_action("Conectar.png", "Conectar", self.connect_nodes, "Conectar")
        
        # Botão ocultar/reexibir
        self.act_hide = make_action("Ocultar.png", "Ocultar ou reexibir objetos", self.toggle_hide_mode, "Ocultar")
        
        self.act_delete = make_action("Excluir.png", "Excluir", self.delete_selected, "Excluir")

        tb.addSeparator()

        self.act_font = make_action("Fonte.png", "Fonte", self.change_font)
        self.act_colors = make_action("Cores.png", "Cores", self.change_colors)

        tb.addSeparator()

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
    
    def reveal_all_items(self):
        """Reexibe todos os objetos ocultos"""
        if self.hide_mode_active:
            self.hide_mode_active = False
            for item in self.hide_mode_hidden_items:
                item.setVisible(True)
            self.hide_mode_hidden_items = []
    
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

        # Botão Conectar: habilitado se há 2+ objetos selecionados (StyledNode ou MediaItem)
        connectable_items = [i for i in sel if isinstance(i, (StyledNode, MediaItem))]
        self.act_connect.setEnabled(len(connectable_items) >= 2)

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
    # TECLAS DE ATALHO
    # --------------------------------------------------
    def keyPressEvent(self, event):
        """Manipula eventos de teclado para movimento dos objetos selecionados ou pan da tela"""
        
        # Tecla + para adicionar objeto
        if event.key() == Qt.Key_Plus:
            self.add_object()
            event.accept()
            return
        
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, (StyledNode, MediaItem))]
        
        # Movimento com setas (10 pixels por vez)
        delta_x = 0
        delta_y = 0
        step = 10
        
        if event.key() == Qt.Key_Left:
            delta_x = step
        elif event.key() == Qt.Key_Right:
            delta_x = -step
        elif event.key() == Qt.Key_Up:
            delta_y = step
        elif event.key() == Qt.Key_Down:
            delta_y = -step
        else:
            super().keyPressEvent(event)
            return
        
        if selected_items:
            # Mover todos os itens selecionados
            for item in selected_items:
                new_pos = item.pos() + QPointF(delta_x, delta_y)
                item.setPos(new_pos)
            event.accept()
        else:
            # Mover a tela (pan) usando scrollbars
            h_scroll = self.view.horizontalScrollBar()
            v_scroll = self.view.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() + delta_x)
            v_scroll.setValue(v_scroll.value() + delta_y)
            self.view._extend_scroll_range_if_needed()
            event.accept()
    
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
            source_rect = source.sceneBoundingRect()
            
            # Verificar espaço ao redor para posicionar o novo objeto
            # Tentar posições: direita, esquerda, abaixo, acima
            candidates = []
            offset = 50  # distância do objeto fonte
            
            # Direita
            candidates.append(QPointF(source_rect.right() + offset, source_rect.top()))
            # Esquerda  
            candidates.append(QPointF(source_rect.left() - offset, source_rect.top()))
            # Abaixo
            candidates.append(QPointF(source_rect.left(), source_rect.bottom() + offset))
            # Acima
            candidates.append(QPointF(source_rect.left(), source_rect.top() - offset))
            
            # Escolher a primeira posição que não colida com outros objetos
            new_pos = None
            for candidate in candidates:
                collides = False
                for item in self.scene.items():
                    if item == source or not hasattr(item, 'sceneBoundingRect'):
                        continue
                    item_rect = item.sceneBoundingRect()
                    # Verificar colisão com margem de 10px
                    if item_rect.adjusted(-10, -10, 10, 10).intersects(source_rect):
                        # Ajustar para posição absoluta
                        test_rect = source_rect.translated(candidate - source_rect.topLeft())
                        if test_rect.adjusted(-10, -10, 10, 10).intersects(item_rect):
                            collides = True
                            break
                if not collides:
                    new_pos = candidate
                    break
            
            # Se todas as posições colidem, usar a posição original (direita)
            if new_pos is None:
                new_pos = candidates[0]
            
            node = StyledNode(new_pos.x(), new_pos.y())
            self.undo_stack.push(AddItemCommand(self.scene, node, "Adicionar objeto", self))
            connection = SmartConnection(source, node)
            self.undo_stack.push(AddItemCommand(self.scene, connection, "Conectar objeto", self))
            # Forçar atualização do caminho da conexão
            connection.update_path()
        else:
            pos = self.view.mapToScene(self.view.viewport().rect().center())
            node = StyledNode(pos.x(), pos.y())
            self.undo_stack.push(AddItemCommand(self.scene, node, "Adicionar objeto", self))

        self.scene.clearSelection()
        node.setSelected(True)
        node.text.setFocus(Qt.OtherFocusReason)

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
        """Conecta ou desconecta objetos selecionados"""
        sel = [i for i in self.scene.selectedItems() if isinstance(i, (StyledNode, MediaItem))]
        
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
        
        # Abrir diálogo
        result = QFontDialog.getFont(target_node.text.font(), self)
        
        # Validar resultado
        if not isinstance(result, tuple) or len(result) != 2:
            return
        
        ok, font = result
        
        if not ok or not isinstance(font, QFont):
            return
        
        # Guardar HTML antes
        old_html = target_node.text.document().toHtml()
        
        if has_text_selection:
            # Aplicar apenas ao texto selecionado
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()
            cursor.setPosition(selection_start)
            cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
            
            # Aplicar formato
            fmt = QTextCharFormat()
            fmt.setFont(font)
            cursor.mergeCharFormat(fmt)
            
            # Atualizar o cursor do texto
            target_node.text.setTextCursor(cursor)
        else:
            # Aplicar a toda a fonte do nó (objeto selecionado sem seleção de texto)
            target_node.text.setFont(font)
        
        # Guardar HTML depois
        new_html = target_node.text.document().toHtml()
        
        # Registrar no undo/redo se houve mudança
        if old_html != new_html:
            self.undo_stack.beginMacro("Mudar fonte")
            cmd = ChangeTextHtmlCommand(target_node, old_html, new_html, "Mudar fonte")
            self.undo_stack.push(cmd)
            self.undo_stack.endMacro()

    def change_colors(self):
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

        # Verificar se há texto selecionado
        cursor = target_node.text.textCursor()
        has_text_selection = cursor.hasSelection()
        
        if has_text_selection:
            # Texto selecionado: mudar cor do texto
            color = QColorDialog.getColor(Qt.black, self, "Cor do texto")
            if not color.isValid():
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
            # Nenhum texto selecionado: mudar cor de fundo do nó
            color = QColorDialog.getColor(Qt.white, self, "Cor de fundo")
            if color.isValid():
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

    def _update_window_title(self):
        """Atualiza a barra de título: Amarelo Mind - nome.amind ou Amarelo Mind"""
        if self.current_file:
            name = os.path.basename(self.current_file)
            self.setWindowTitle(f"Amarelo Mind - {name}")
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
        image.fill(QColor("#f7d5a1"))

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
        from PySide6.QtCore import Qt, QEvent
        
        all_buttons = [
            "Novo", "Abrir", "Salvar", "Exportar", "Desfazer", "Refazer",
            "Copiar", "Colar", "Adicionar", "Mídia", "Conectar", "Ocultar",
            "Excluir", "Fonte", "Cores", "Localizar"
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
            shortcut_edit.setMinimumWidth(120)
            shortcut_edits[name] = shortcut_edit
            table.setCellWidget(i, 1, shortcut_edit)
        
        table.resizeRowsToContents()
        layout.addWidget(table)
        
        info_label = QLabel("Dica: Pressione Escape para limpar. Selecione a linha e digite as teclas.")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)
        
        btn_layout = QHBoxLayout()
        
        selected_row = [0]
        
        def handle_key_event(event):
            row = table.currentRow()
            if row < 0:
                return False
            
            key = event.key()
            modifiers = event.modifiers()
            
            if key == Qt.Key_Escape:
                shortcut_edits[all_buttons[row]].setText("")
                event.accept()
                return True
            
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, 
                       Qt.Key_Tab, Qt.Key_Backtab, Qt.Key_Return, Qt.Key_Enter):
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
                shortcut_edits[all_buttons[row]].setText("+".join(combo))
                event.accept()
                return True
            
            return False
        
        dialog.keyPressEvent = handle_key_event
        
        def apply_shortcuts():
            for name, edit in shortcut_edits.items():
                self.custom_shortcuts[name] = edit.text()
            
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
            
            if hasattr(self, 'act_media'):
                self.act_media.setShortcut(self.custom_shortcuts.get("Mídia", ""))
            
            self.act_connect.setShortcut(self.custom_shortcuts.get("Conectar", ""))
            self.act_delete.setShortcut(self.custom_shortcuts.get("Excluir", ""))
            
            if hasattr(self, 'act_font'):
                self.act_font.setShortcut(self.custom_shortcuts.get("Fonte", ""))
            
            if hasattr(self, 'act_colors'):
                self.act_colors.setShortcut(self.custom_shortcuts.get("Cores", ""))
            
            self.act_search.setShortcut(self.custom_shortcuts.get("Localizar", ""))
        
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

<p><b>Versão 1.0.0</b></p>

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


  # ======================================================
  # MAIN
  # ======================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Estilo global e configuração
    app.setStyle("Fusion")
    
    # Registrar ícone para arquivos .amind (Windows only)
    try:
        from register_icon import register_icon
        register_icon()
    except Exception as e:
        print(f"Aviso: Não foi possível registrar ícone .amind: {e}")
    
    window = AmareloMainWindow()
    window.show()
    
    sys.exit(app.exec())
