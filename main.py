import sys
import os
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QToolBar, QFileDialog, QFrame, QFontDialog, QColorDialog,
    QMessageBox, QGraphicsTextItem, QDialog, QInputDialog
)
from PySide6.QtCore import Qt, QSize, QPointF, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QAction, QWheelEvent,
    QUndoStack, QImage, QUndoCommand, QFont,
    QTextCursor, QTextCharFormat, QPen
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
        if self.window and isinstance(self.item, StyledNode):
            if hasattr(self.item.text, 'selectionChanged'):
                self.item.text.selectionChanged.connect(self.window.update_button_states)

    def undo(self):
        self.scene.removeItem(self.item)


class RemoveItemCommand(QUndoCommand):
    """Comando para remover um item da cena"""
    def __init__(self, scene, item, description="Remover objeto"):
        super().__init__(description)
        self.scene = scene
        self.item = item

    def redo(self):
        self.scene.removeItem(self.item)

    def undo(self):
        self.scene.addItem(self.item)


class MoveItemCommand(QUndoCommand):
    """Comando para mover um item na cena"""
    def __init__(self, item, old_pos, new_pos, description="Mover objeto"):
        super().__init__(description)
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.item.setPos(self.new_pos)

    def undo(self):
        self.item.setPos(self.old_pos)



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
        
        if not isinstance(item_clicked, (StyledNode, Handle)):
            # Clicou fora de qualquer item útil, limpar seleção de texto
            for item in self.scene().items():
                if isinstance(item, StyledNode):
                    cursor = item.text.textCursor()
                    if cursor.hasSelection():
                        cursor.clearSelection()
                        item.text.setTextCursor(cursor)
        
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
                    item.setPos(new_pos)
            
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
        
        # Se estava arrastando um item
        if self._dragging_item and event.button() == Qt.LeftButton:
            # Se não foi um drag real (apenas um clique), restaurar posições originais
            if not self._is_dragging:
                for item, original_pos in self._item_positions.items():
                    item.setPos(original_pos)
            
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
        
        # Conectar sinais para detectar mudanças
        self.undo_stack.indexChanged.connect(self._on_undo_stack_changed)
        self._last_autosave_index = 0

        # Alinhar ativo por padrão
        self.alinhar_ativo = True

        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.view = InfiniteCanvas(self.scene, self)
        self.view.set_undo_stack(self.undo_stack)
        self.setCentralWidget(self.view)
        
        # Filtro de itens
        self.item_filter = ItemFilter(self.scene)

        self.load_styles()
        self.setup_toolbar()

        self.scene.selectionChanged.connect(self.update_button_states)
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
        """Executa autosave se houver mudanças e arquivo estiver salvo"""
        if self.autosave_enabled and self.current_file and self.undo_stack.canUndo():
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

    # --------------------------------------------------
    # TOOLBAR
    # --------------------------------------------------
    def setup_toolbar(self):
        tb = QToolBar()
        tb.setIconSize(QSize(40, 40))
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.addToolBar(tb)

        def make_action(icon, tooltip, slot, shortcut=None):
            act = QAction(IconManager.load_icon(icon, icon[0]), "", self)
            act.setToolTip(tooltip)
            if shortcut:
                act.setShortcut(shortcut)
            act.triggered.connect(slot)
            tb.addAction(act)
            return act

        make_action("Novo.png", "Novo mapa mental", self.new_window, "Ctrl+N")
        make_action("Abrir.png", "Abrir mapa mental", self.open_project, "Ctrl+A")
        make_action("Salvar.png", "Salvar alterações", self.save_project, "Ctrl+S")
        self.act_export = make_action("Exportar.png", "Exportar como imagem", self.export_png)

        tb.addSeparator()

        self.act_undo = self.undo_stack.createUndoAction(self, "")
        self.act_undo.setToolTip("Desfazer (Ctrl+Z)")
        self.act_undo.setIcon(IconManager.load_icon("Desfazer.png", "D"))
        self.act_undo.setShortcut("Ctrl+Z")
        tb.addAction(self.act_undo)

        self.act_redo = self.undo_stack.createRedoAction(self, "")
        self.act_redo.setToolTip("Refazer (Ctrl+R)")
        self.act_redo.setIcon(IconManager.load_icon("Refazer.png", "R"))
        self.act_redo.setShortcut("Ctrl+R")
        tb.addAction(self.act_redo)

        tb.addSeparator()

        make_action("Copiar.png", "Copiar", self.copy_content, "Ctrl+C")
        make_action("Colar.png", "Colar", self.paste_content, "Ctrl+V")

        tb.addSeparator()

        make_action("Adicionar.png", "Adicionar objeto", self.add_object, "+")
        make_action("Conectar.png", "Conectar", self.connect_nodes, "C")
        make_action("Excluir.png", "Excluir", self.delete_selected, "Delete")

        tb.addSeparator()

        # Botão Midia
        self.act_media = make_action("Midia.png", "Mídia", self.insert_media)

        tb.addSeparator()

        self.act_font = make_action("Fonte.png", "Fonte", self.change_font)
        self.act_colors = make_action("Cores.png", "Cores", self.change_colors)
        self.act_shadow = make_action("Sombra.png", "Sombra", self.toggle_shadow)

        tb.addSeparator()

        self.act_align = QAction(
            IconManager.load_icon("Alinhar.png", "A"),
            "",
            self
        )
        self.act_align.setToolTip("Alinhar")
        self.act_align.setCheckable(True)
        self.act_align.setChecked(True)
        self.act_align.triggered.connect(self.toggle_align)
        tb.addAction(self.act_align)

        tb.addSeparator()

        # Botão Procurar
        self.act_search = make_action("lupa.png", "Procurar (Ctrl+F)", self.show_search_dialog, "Ctrl+F")

    # --------------------------------------------------
    # ESTADOS
    # --------------------------------------------------
    def update_button_states(self):
        try:
            sel = self.scene.selectedItems()
        except RuntimeError:
            return

        has_sel = bool(sel)
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
        self.act_shadow.setEnabled(has_styled_node and not has_media_selected)
        self.act_export.setEnabled(has_items)

    def insert_media(self):
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
            for u in urls:
                try:
                    with urllib.request.urlopen(u) as resp:
                        data = resp.read()
                    img = QImage()
                    img.loadFromData(data)
                    if not img.isNull():
                        img_pairs.append((img, u))
                    else:
                        # Áudio/Vídeo por URL ainda não implementados
                        pass
                except Exception:
                    pass
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
        """Manipula eventos de teclado para movimento dos objetos selecionados"""
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, (StyledNode, MediaItem))]
        
        if not selected_items:
            super().keyPressEvent(event)
            return
        
        # Movimento com setas (10 pixels por vez)
        delta_x = 0
        delta_y = 0
        step = 10
        
        if event.key() == Qt.Key_Left:
            delta_x = -step
        elif event.key() == Qt.Key_Right:
            delta_x = step
        elif event.key() == Qt.Key_Up:
            delta_y = -step
        elif event.key() == Qt.Key_Down:
            delta_y = step
        else:
            super().keyPressEvent(event)
            return
        
        # Mover todos os itens selecionados
        for item in selected_items:
            new_pos = item.pos() + QPointF(delta_x, delta_y)
            item.setPos(new_pos)
        
        event.accept()
    
    # --------------------------------------------------
    # FUNCIONALIDADES
    # --------------------------------------------------
    def new_window(self):
        """Abre uma nova janela completamente independente."""
        try:
            new_win = AmareloMainWindow()
            new_win.show()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir uma nova janela: {e}")


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
        for item in self.item_filter.get_filtered_items():
            if isinstance(item, StyledNode):
                item.set_node_type(style_type)

    def add_object(self):
        sel = self.scene.selectedItems()

        if len(sel) == 1 and isinstance(sel[0], (StyledNode, MediaItem)):
            source = sel[0]
            pos = source.pos() + QPointF(source.rect().width() + 20, 0)
            node = StyledNode(pos.x(), pos.y(), brush=source.brush())
            self.undo_stack.push(AddItemCommand(self.scene, node, "Adicionar objeto", self))
            connection = SmartConnection(source, node)
            self.undo_stack.push(AddItemCommand(self.scene, connection, "Conectar objeto", self))
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
            elif isinstance(item, StyledNode):
                # Remover conexões conectadas ao nó
                for conn in self.scene.items():
                    if isinstance(conn, SmartConnection) and conn not in seen_conn and (conn.source == item or conn.target == item):
                        seen_conn.add(conn)
                        self.undo_stack.push(RemoveItemCommand(self.scene, conn, "Remover conexão"))
                # Remover o nó
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
            cursor = focus_item.textCursor()
            cursor.insertText(text)
            focus_item.setTextCursor(cursor)
            return

        # 2. Cola no nó selecionado
        sel = [i for i in self.scene.selectedItems() if isinstance(i, StyledNode)]
        if not sel:
            return
        node = sel[0]
        cursor = node.text.textCursor()
        cursor.insertText(text)
        node.text.setTextCursor(cursor)

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

        # CAPTURAR INFORMAÇÕES DA SELEÇÃO ANTES DO DIÁLOGO
        cursor = target_node.text.textCursor()
        has_text_selection = cursor.hasSelection()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()
        
        # Abrir diálogo
        result = QFontDialog.getFont(target_node.text.font(), self)
        
        # Validar resultado
        if not isinstance(result, tuple) or len(result) != 2:
            return
        
        ok, font = result  # ORDEM CORRETA: (ok, font)
        
        if not ok or not isinstance(font, QFont):
            return

        # Guardar HTML antes
        old_html = target_node.text.document().toHtml()
        
        if has_text_selection:
            # Aplicar apenas ao texto selecionado
            cursor = target_node.text.textCursor()
            cursor.setPosition(selection_start)
            cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
            
            # Aplicar formato
            fmt = QTextCharFormat()
            fmt.setFont(font)
            cursor.mergeCharFormat(fmt)
            
            # Atualizar o cursor do texto
            target_node.text.setTextCursor(cursor)
        else:
            # Aplicar a toda a fonte do nó
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
        for item in self.scene.selectedItems():
            if isinstance(item, StyledNode):
                item.toggle_shadow()

    def toggle_align(self):
        self.alinhar_ativo = self.act_align.isChecked()

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
