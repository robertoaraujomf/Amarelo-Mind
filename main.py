import sys
import os
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QToolBar, QFileDialog, QFrame, QFontDialog, QColorDialog,
    QMessageBox, QGraphicsTextItem
)
from PySide6.QtCore import Qt, QSize, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QAction, QWheelEvent,
    QUndoStack, QImage, QUndoCommand, QFont,
    QTextCursor, QTextCharFormat
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
from items.node_styles import NODE_STATE
from items.group_item import GroupNode
from core.connection import SmartConnection


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

    def undo(self):
        self.item.text.setHtml(self.old_html)


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
    def __init__(self, scene, item, description="Adicionar objeto"):
        super().__init__(description)
        self.scene = scene
        self.item = item

    def redo(self):
        self.scene.addItem(self.item)

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

        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform
        )

        self.setBackgroundBrush(QColor("#f7d5a1"))
        self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # essencial para seleção retangular
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)

        self._panning = False
        self._last_pos = None
        self.undo_stack = None
        self._item_positions = {}  # Rastreia posições originais para Undo/Redo

    def set_undo_stack(self, undo_stack):
        """Define o stack de Undo/Redo"""
        self.undo_stack = undo_stack

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        """
        Controle do mouse:
        - Botão esquerdo: move objeto, seleciona, ou pan (se vazio)
        - Botão direito: seleção retangular
        """
        # BOTÃO DIREITO: Seleção retangular
        if event.button() == Qt.RightButton:
            # Se clicou em um Handle, permite resize
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, Handle):
                super().mousePressEvent(event)
                return

            # Inicia seleção retangular com o botão direito
            self.setDragMode(QGraphicsView.RubberBandDrag)
            super().mousePressEvent(event)
            return

        # BOTÃO ESQUERDO
        if event.button() == Qt.LeftButton:
            item_clicked = self.itemAt(event.position().toPoint())
            
            # Se clicou em um item
            if item_clicked:
                # Se não está selecionado e Ctrl não foi pressionado, deseleciona outros
                if not item_clicked.isSelected() and not (event.modifiers() & Qt.ControlModifier):
                    self.scene().clearSelection()
                
                # Registra a posição original para movimento
                if hasattr(item_clicked, 'setPos'):
                    self._item_positions[item_clicked] = item_clicked.pos()
                
                # Processa o clique normal (seleção)
                super().mousePressEvent(event)
                return
            
            # Se não clicou em item e não há seleção: inicia pan
            if not self.scene().selectedItems():
                self._panning = True
                self._last_pos = event.position().toPoint()
                self.setCursor(Qt.ClosedHandCursor)
                return
            
            # Se há seleção, processa clique normal (deseleciona)
            super().mousePressEvent(event)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Se está fazendo pan
        if self._panning:
            delta = event.position().toPoint() - self._last_pos
            self._last_pos = event.position().toPoint()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Se estava fazendo pan
        if self._panning and event.button() == Qt.LeftButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            self._item_positions.clear()
            return

        # Se era seleção retangular com botão direito
        if event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.NoDrag)
            super().mouseReleaseEvent(event)
            return

        # Se estava movendo um item com botão esquerdo
        if event.button() == Qt.LeftButton:
            # Registra movimento no Undo/Redo se o item foi movido
            if self._item_positions:
                for item, old_pos in self._item_positions.items():
                    new_pos = item.pos()
                    if old_pos != new_pos and self.undo_stack:
                        cmd = MoveItemCommand(item, old_pos, new_pos, "Mover objeto")
                        self.undo_stack.push(cmd)
                self._item_positions.clear()
            
            super().mouseReleaseEvent(event)
            return

        super().mouseReleaseEvent(event)


# ======================================================
# JANELA PRINCIPAL
# ======================================================
class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Amarelo Mind")
        self.setWindowIcon(IconManager.load_icon("App_icon.png"))

        self.undo_stack = QUndoStack(self)
        self.current_file = None
        self.groups = []
        
        # Gerenciador de persistência
        self.persistence = PersistenceManager()

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
        self.update_button_states()

        self.showMaximized()

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

        # Shortcuts for node styles (1-9)
        for name, idx in NODE_STATE.items():
            if idx > 0 and idx <= 9:
                act = QAction(self)
                act.setShortcut(f"{idx}")
                act.triggered.connect(lambda checked=False, n=name: self.set_node_style(n))
                self.addAction(act)

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
        self.act_undo.setToolTip("Desfazer")
        self.act_undo.setIcon(IconManager.load_icon("Desfazer.png", "D"))
        tb.addAction(self.act_undo)

        self.act_redo = self.undo_stack.createRedoAction(self, "")
        self.act_redo.setToolTip("Refazer")
        self.act_redo.setIcon(IconManager.load_icon("Refazer.png", "R"))
        tb.addAction(self.act_redo)

        tb.addSeparator()

        make_action("Copiar.png", "Copiar", self.copy_content, "Ctrl+C")
        make_action("Colar.png", "Colar", self.paste_content, "Ctrl+V")

        tb.addSeparator()

        make_action("Adicionar.png", "Adicionar objeto", self.add_object, "+")
        self.act_group = make_action("Agrupar.png", "Agrupar", self.toggle_group)
        make_action("Conectar.png", "Conectar", self.connect_nodes, "C")
        make_action("Excluir.png", "Excluir", self.delete_selected, "Delete")

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
        
        # Check focus for text editing
        focus_item = self.scene.focusItem()
        is_text_focus = isinstance(focus_item, QGraphicsTextItem)
        
        can_edit_style = has_sel or is_text_focus

        self.act_font.setEnabled(can_edit_style)
        self.act_colors.setEnabled(can_edit_style)
        self.act_shadow.setEnabled(has_sel)
        self.act_group.setEnabled(len(sel) > 1)
        self.act_export.setEnabled(has_items)

    # --------------------------------------------------
    # FUNCIONALIDADES
    # --------------------------------------------------
    def new_window(self):
        """Abre nova janela com canvas vazio; mantém a atual aberta com seu conteúdo."""
        win = AmareloMainWindow()
        win.current_file = None
        win._update_window_title()
        win.show()
        win.raise_()
        win.activateWindow()

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

        if len(sel) == 1 and isinstance(sel[0], StyledNode):
            source = sel[0]
            pos = source.pos() + QPointF(source.rect().width() + 20, 0)
            node = StyledNode(pos.x(), pos.y(), brush=source.brush())
            self.undo_stack.push(AddItemCommand(self.scene, node, "Adicionar objeto"))
            connection = SmartConnection(source, node)
            self.undo_stack.push(AddItemCommand(self.scene, connection, "Conectar objeto"))
        else:
            pos = self.view.mapToScene(self.view.viewport().rect().center())
            node = StyledNode(pos.x(), pos.y())
            self.undo_stack.push(AddItemCommand(self.scene, node, "Adicionar objeto"))

        self.scene.clearSelection()
        node.setSelected(True)
        node.text.setFocus(Qt.OtherFocusReason)

    def delete_selected(self):
        to_remove = list(self.scene.selectedItems())
        seen_conn = set()
        for item in to_remove:
            if isinstance(item, StyledNode):
                for conn in self.scene.items():
                    if isinstance(conn, SmartConnection) and conn not in seen_conn and (conn.source == item or conn.target == item):
                        seen_conn.add(conn)
                        self.undo_stack.push(RemoveItemCommand(self.scene, conn, "Remover conexão"))
            self.undo_stack.push(RemoveItemCommand(self.scene, item, "Remover objeto"))

    def toggle_group(self):
        sel = self.scene.selectedItems()
        if not sel:
            return

        if isinstance(sel[0].parentItem(), GroupNode):
            group = sel[0].parentItem()
            group.ungroup()
            self.undo_stack.push(RemoveItemCommand(self.scene, group, "Desagrupar"))
        else:
            group = GroupNode(sel)
            self.undo_stack.push(AddItemCommand(self.scene, group, "Agrupar"))

    def connect_nodes(self):
        sel = [i for i in self.scene.selectedItems() if isinstance(i, StyledNode)]
        for i in range(len(sel) - 1):
            connection = SmartConnection(sel[i], sel[i + 1])
            self.undo_stack.push(AddItemCommand(self.scene, connection, "Conectar nós"))

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
        result = QFontDialog.getFont(QFont(), self)
        if isinstance(result, tuple):
            font, ok = result
        else:
            font = result
            ok = isinstance(font, QFont) and font is not None
        
        if not ok or not isinstance(font, QFont):
            return

        targets = []
        focus_item = self.scene.focusItem()
        if isinstance(focus_item, QGraphicsTextItem):
            parent = focus_item.parentItem()
            if isinstance(parent, StyledNode):
                targets.append(parent)
        
        for item in self.scene.selectedItems():
            if isinstance(item, StyledNode) and item not in targets:
                targets.append(item)

        if not targets:
            return

        self.undo_stack.beginMacro("Mudar fonte")
        for item in targets:
            cursor = item.text.textCursor()
            if cursor.hasSelection():
                old_html = item.text.document().toHtml()
                fmt = QTextCharFormat()
                fmt.setFont(font)
                cursor.mergeCharFormat(fmt)
                new_html = item.text.document().toHtml()
                cmd = ChangeTextHtmlCommand(item, old_html, new_html, "Mudar fonte")
                self.undo_stack.push(cmd)
            else:
                old_font = item.text.font()
                item.set_font(font)
                cmd = ChangeFontCommand(item, old_font, font, "Mudar fonte")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def change_colors(self):
        targets = []
        focus_item = self.scene.focusItem()
        if isinstance(focus_item, QGraphicsTextItem):
            parent = focus_item.parentItem()
            if isinstance(parent, StyledNode):
                targets.append(parent)
        
        for item in self.scene.selectedItems():
            if isinstance(item, StyledNode) and item not in targets:
                targets.append(item)

        if not targets:
            return

        has_text_sel = any(it.text.textCursor().hasSelection() for it in targets)
        if has_text_sel:
            color = QColorDialog.getColor(Qt.black, self, "Cor da fonte")
            if not color.isValid():
                return
            
            self.undo_stack.beginMacro("Mudar cor do texto")
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            for item in targets:
                cursor = item.text.textCursor()
                if cursor.hasSelection():
                    old_html = item.text.document().toHtml()
                    cursor.mergeCharFormat(fmt)
                    new_html = item.text.document().toHtml()
                    cmd = ChangeTextHtmlCommand(item, old_html, new_html, "Mudar cor do texto")
                    self.undo_stack.push(cmd)
            self.undo_stack.endMacro()
        else:
            color = QColorDialog.getColor(Qt.white, self, "Cor de fundo")
            if color.isValid():
                self.undo_stack.beginMacro("Mudar cor de fundo")
                for item in targets:
                    old_state = {'node_type': item.node_type, 'custom_color': item.custom_color}
                    new_state = {'node_type': item.node_type, 'custom_color': color.name()}
                    cmd = ChangeNodeStyleCommand(item, old_state, new_state)
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
            self._update_window_title()
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar o projeto.")

    def open_project(self):
        """Abre um projeto salvo"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Projeto", "", "Amarelo Mind (*.amind);;JSON (*.json)"
        )
        if not path:
            return

        self.current_file = path
        if self.persistence.load_from_file(path, self.scene):
            self._update_window_title()
        else:
            QMessageBox.critical(self, "Erro", "Falha ao carregar o projeto.")

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


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AmareloMainWindow()
    win.show()
    sys.exit(app.exec())
