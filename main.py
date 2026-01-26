import sys
import os
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QToolBar, QFileDialog, QFrame, QFontDialog, QColorDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QPainter, QColor, QAction, QWheelEvent,
    QUndoStack, QImage
)

# ======================================================
# PATHS / ÍCONES
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from core.icon_manager import IconManager
IconManager.set_icons_base(BASE_DIR)

from items.shapes import StyledNode
from items.group_item import GroupNode
from core.connection import SmartConnection


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

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        # pan apenas em área vazia e sem seleção
        if (
            event.button() == Qt.LeftButton
            and not self.itemAt(event.position().toPoint())
            and not self.scene().selectedItems()
        ):
            self._panning = True
            self._last_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
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
        self._panning = False
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)


# ======================================================
# JANELA PRINCIPAL
# ======================================================
class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Amarelo Mind")

        self.undo_stack = QUndoStack(self)
        self.current_file = None
        self.groups = []

        # Alinhar ativo por padrão
        self.alinhar_ativo = True

        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.view = InfiniteCanvas(self.scene, self)
        self.setCentralWidget(self.view)

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

        self.act_font.setEnabled(has_sel)
        self.act_colors.setEnabled(has_sel)
        self.act_shadow.setEnabled(has_sel)
        self.act_group.setEnabled(len(sel) > 1)
        self.act_export.setEnabled(has_items)

    # --------------------------------------------------
    # FUNCIONALIDADES
    # --------------------------------------------------
    def new_window(self):
        AmareloMainWindow().show()

    def add_object(self):
        sel = self.scene.selectedItems()

        if len(sel) == 1 and isinstance(sel[0], StyledNode):
            source = sel[0]
            pos = source.pos() + source.boundingRect().bottomRight()
            node = StyledNode(pos.x(), pos.y())
            self.scene.addItem(node)
            self.scene.addItem(SmartConnection(source, node))
        else:
            pos = self.view.mapToScene(self.view.viewport().rect().center())
            node = StyledNode(pos.x(), pos.y())
            self.scene.addItem(node)

        node.setSelected(True)
        node.text.setFocus(Qt.OtherFocusReason)

    def delete_selected(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)

    def toggle_group(self):
        sel = self.scene.selectedItems()
        if not sel:
            return

        if isinstance(sel[0].parentItem(), GroupNode):
            group = sel[0].parentItem()
            group.ungroup()
            self.scene.removeItem(group)
        else:
            group = GroupNode(sel)
            self.scene.addItem(group)

    def connect_nodes(self):
        sel = [i for i in self.scene.selectedItems() if isinstance(i, StyledNode)]
        for i in range(len(sel) - 1):
            self.scene.addItem(SmartConnection(sel[i], sel[i + 1]))

    def copy_content(self):
        sel = self.scene.selectedItems()
        if len(sel) == 1 and isinstance(sel[0], StyledNode):
            QApplication.clipboard().setText(sel[0].get_text())

    def paste_content(self):
        sel = self.scene.selectedItems()
        if len(sel) == 1 and isinstance(sel[0], StyledNode):
            sel[0].set_text(QApplication.clipboard().text())

    def change_font(self):
        font, ok = QFontDialog.getFont(self)
        if ok:
            for item in self.scene.selectedItems():
                if isinstance(item, StyledNode):
                    item.set_font(font)

    def change_colors(self):
        color = QColorDialog.getColor(Qt.white, self)
        if color.isValid():
            for item in self.scene.selectedItems():
                if isinstance(item, StyledNode):
                    item.set_background(color)

    def toggle_shadow(self):
        for item in self.scene.selectedItems():
            item.toggle_shadow()

    def toggle_align(self):
        self.alinhar_ativo = not self.alinhar_ativo
        self.act_align.setChecked(self.alinhar_ativo)

    def save_project(self):
        QMessageBox.information(self, "Salvar", "Salvar ainda não implementado.")

    def open_project(self):
        QMessageBox.information(self, "Abrir", "Abrir ainda não implementado.")

    def export_png(self):
        if not self.scene.items():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar PNG", "", "PNG (*.png)"
        )
        if not path:
            return

        rect = self.scene.itemsBoundingRect()
        image = QImage(
            int(rect.width()),
            int(rect.height()),
            QImage.Format_ARGB32
        )
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.translate(-rect.topLeft())
        self.scene.render(painter)
        painter.end()

        image.save(path)


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AmareloMainWindow()
    win.show()
    sys.exit(app.exec())
