import sys
import os
from PySide6.QtWidgets import (QMainWindow, QApplication, QGraphicsView, 
                             QGraphicsScene, QFileDialog, QToolBar,
                             QStatusBar, QWidget, QHBoxLayout, QLineEdit, 
                             QLabel, QFrame, QStyle, QComboBox, QFontDialog, QColorDialog)
from PySide6.QtCore import Qt, QRectF, QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QImage, QIcon, QAction, QWheelEvent, QKeyEvent, QUndoStack, QPen, QFont, QPixmap

# Certifique-se de que estes módulos existam no seu diretório de projeto
try:
    from core.icon_manager import IconManager
    from items.connection_label import ConnectionLabel
    from items.group_box import GroupBox
    from core.text_editor import TextEditorManager
    from core.style_manager import StyleManager
    from items.shapes import StyledNode as MindMapNode
    from core.connection import SmartConnection
    from core.persistence import PersistenceManager
except ImportError as e:
    print(f"Erro de importação crítica: {e}")
    MindMapNode = None
    SmartConnection = None
    PersistenceManager = None

class InfiniteCanvas(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setBackgroundBrush(QColor("#e5e0d9")) 
        self.setFrameStyle(QFrame.NoFrame)
        self.setDragMode(QGraphicsView.RubberBandDrag) 
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if self.itemAt(event.position().toPoint()):
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setDragMode(QGraphicsView.RubberBandDrag)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        sel = self.scene().selectedItems()
        if sel:
            step = 15
            key = event.key()
            if key == Qt.Key.Key_Up:
                for item in sel: item.moveBy(0, -step)
                return 
            elif key == Qt.Key.Key_Down:
                for item in sel: item.moveBy(0, step)
                return
            elif key == Qt.Key.Key_Left:
                for item in sel: item.moveBy(-step, 0)
                return
            elif key == Qt.Key.Key_Right:
                for item in sel: item.moveBy(step, 0)
                return
        super().keyPressEvent(event)

class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amarelo Mind")
        self.undo_stack = QUndoStack(self)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #2d2d2d; }
            QToolBar { background-color: #1a1a1a; border-bottom: 2px solid #f2f71d; padding: 5px; }
            QStatusBar { background-color: #1a1a1a; color: #f2f71d; border-top: 1px solid #f2f71d; }
            QLabel { color: #f5f0e9; font-size: 10px; }
            QLineEdit { background-color: #3d3d3d; color: #f2f71d; border: 1px solid #555; border-radius: 4px; padding: 2px; }
        """)

        self.scene = QGraphicsScene(-10**6, -10**6, 2*10**6, 2*10**6)
        self.view = InfiniteCanvas(self.scene, self)
        self.setCentralWidget(self.view)

        if PersistenceManager:
            self.persistence = PersistenceManager(self.scene)

        self.setup_toolbar()
        self.setup_statusbar()
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.showMaximized()

    # --- ÍCONES ---
    def draw_custom_node_icon(self):
        pixmap = QPixmap(32, 32); pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap); painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#f2f71d")); painter.setPen(QPen(Qt.GlobalColor.black, 1.5))
        painter.drawRoundedRect(4, 4, 24, 24, 6, 6)
        painter.end(); return QIcon(pixmap)

    def draw_venn_icon(self):
        pixmap = QPixmap(32, 32); pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap); painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setBrush(QColor(242, 247, 29, 150))
        painter.drawEllipse(4, 8, 16, 16); painter.drawEllipse(12, 8, 16, 16)
        painter.end(); return QIcon(pixmap)

    def draw_shadow_icon(self):
        pixmap = QPixmap(32, 32); pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap); painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(50, 50, 50, 150)); painter.setPen(Qt.GlobalColor.transparent)
        painter.drawEllipse(6, 22, 20, 6)
        painter.setBrush(QColor("#f2f71d")); painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(8, 4, 16, 16)
        painter.end(); return QIcon(pixmap)

    def draw_text_icon(self, text):
        pixmap = QPixmap(32, 32); pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap); painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end(); return QIcon(pixmap)

    def setup_toolbar(self):
        self.toolbar = QToolBar("Menu Principal")
        self.toolbar.setIconSize(QSize(24, 24)); self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # Arquivo
        self.add_btn(QStyle.StandardPixmap.SP_FileIcon, "Novo", self.new_project, "Ctrl+N")
        self.add_btn(QStyle.StandardPixmap.SP_DialogOpenButton, "Abrir", self.open_project, "Ctrl+O")
        self.add_btn(QStyle.StandardPixmap.SP_DialogSaveButton, "Salvar", self.save_project, "Ctrl+S")
        self.add_btn(QStyle.StandardPixmap.SP_DialogApplyButton, "Exportar PNG", self.export_project, "Ctrl+E")
        self.toolbar.addSeparator()

        # Histórico
        self.add_btn(QStyle.StandardPixmap.SP_ArrowBack, "Desfazer", self.undo, "Ctrl+Z")
        self.add_btn(QStyle.StandardPixmap.SP_ArrowForward, "Refazer", self.redo, "Ctrl+R")
        self.toolbar.addSeparator()

        # Estrutura
        self.toolbar.addAction(QAction(self.draw_custom_node_icon(), "Inserir Nó (N)", self, shortcut="N", triggered=self.add_node))
        self.add_btn(QStyle.StandardPixmap.SP_TitleBarNormalButton, "Duplicar (+)", self.duplicate_node, "+") 
        self.toolbar.addAction(QAction(self.draw_venn_icon(), "Agrupar/Desagrupar (G)", self, shortcut="G", triggered=self.group_selected))
        self.add_btn(QStyle.StandardPixmap.SP_BrowserReload, "Conectar (L)", self.connect_nodes, "L")
        self.add_btn(QStyle.StandardPixmap.SP_FileDialogDetailedView, "Legenda", self.add_line_label) 
        self.add_btn(QStyle.StandardPixmap.SP_TrashIcon, "Excluir (Del)", self.delete_selected, "Delete")
        self.toolbar.addSeparator()

        # Texto
        self.toolbar.addAction(QAction(self.draw_text_icon("F"), "Fonte", self, triggered=self.choose_font))
        self.toolbar.addSeparator()

        # Estética
        self.add_btn(QStyle.StandardPixmap.SP_DialogResetButton, "Cor do objeto", self.change_node_color)
        self.toolbar.addAction(QAction(self.draw_shadow_icon(), "Sombra", self, triggered=self.apply_node_shadow))

    def add_btn(self, style_pixmap, tooltip, callback, shortcut=None):
        icon = self.style().standardIcon(style_pixmap)
        action = QAction(icon, "", self)
        action.setToolTip(tooltip); action.triggered.connect(callback)
        if shortcut: action.setShortcut(shortcut)
        self.toolbar.addAction(action)

    def setup_statusbar(self):
        self.status = QStatusBar(); self.setStatusBar(self.status)
        container = QWidget(); layout = QHBoxLayout(container)
        self.in_x = QLineEdit(); self.in_y = QLineEdit()
        self.in_w = QLineEdit(); self.in_h = QLineEdit()
        for label, edit in zip(["X:", "Y:", "W:", "H:"], [self.in_x, self.in_y, self.in_w, self.in_h]):
            layout.addWidget(QLabel(label)); edit.setFixedWidth(60)
            edit.returnPressed.connect(self.apply_status_changes); layout.addWidget(edit)
        self.status.addPermanentWidget(container)

    # --- LÓGICAS ---
    def undo(self): self.undo_stack.undo()
    def redo(self): self.undo_stack.redo()
    def new_project(self): os.startfile(sys.argv[0])

    def save_project(self):
        if hasattr(self, 'persistence'):
            path, _ = QFileDialog.getSaveFileName(self, "Salvar Mapa", "", "Amarelo Mind (*.amind)")
            if path: self.persistence.save_to_file(path)

    def open_project(self):
        if hasattr(self, 'persistence'):
            path, _ = QFileDialog.getOpenFileName(self, "Abrir Mapa", "", "Amarelo Mind (*.amind)")
            if path: self.persistence.load_from_file(path)

    def add_node(self):
        if MindMapNode:
            visible_rect = self.view.viewport().rect()
            scene_center = self.view.mapToScene(visible_rect.center())
            node = MindMapNode(scene_center.x() - 75, scene_center.y() - 40)
            self.scene.addItem(node); self.scene.clearSelection(); node.setSelected(True)

    def duplicate_node(self):
        for item in self.scene.selectedItems():
            if isinstance(item, MindMapNode):
                new_node = MindMapNode(item.pos().x() + 30, item.pos().y() + 30)
                self.scene.addItem(new_node)

    def delete_selected(self):
        for item in self.scene.selectedItems(): self.scene.removeItem(item)

    def connect_nodes(self):
        sel = self.scene.selectedItems()
        if len(sel) >= 2:
            for i in range(len(sel)-1):
                conn = SmartConnection(sel[i], sel[i+1]); self.scene.addItem(conn)

    def add_line_label(self):
        for item in self.scene.selectedItems():
            if isinstance(item, SmartConnection):
                label = ConnectionLabel("Link", item); item.label = label; label.update_position()

    def group_selected(self):
        sel = self.scene.selectedItems()
        for item in sel:
            if isinstance(item, GroupBox):
                self.scene.removeItem(item); return
        if not sel: return
        rect = sel[0].sceneBoundingRect()
        for item in sel: rect = rect.united(item.sceneBoundingRect())
        rect.adjust(-20, -20, 20, 20); group = GroupBox(rect); self.scene.addItem(group)

    def export_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar", "", "PNG (*.png)")
        if path:
            rect = self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
            img = QImage(rect.size().toSize(), QImage.Format_ARGB32); img.fill(Qt.GlobalColor.white)
            painter = QPainter(img); self.scene.render(painter, QRectF(img.rect()), rect)
            painter.end(); img.save(path)

    def choose_font(self):
        sel = self.scene.selectedItems()
        if not sel: return
        
        # Pegamos o estilo atual do primeiro item para carregar o diálogo com as configs atuais
        current_font = QFont()
        current_color = QColor(Qt.GlobalColor.black)
        
        if hasattr(sel[0], 'text_item'):
            current_font = sel[0].text_item.font()
            current_color = sel[0].text_item.defaultTextColor()

        # 1. Abre o Diálogo de Fonte (Já inclui: Família, Negrito, Itálico, Sublinhado e Riscado)
        font, ok = QFontDialog.getFont(current_font, self, "Configurar Texto")
        
        if ok:
            # 2. Abre o Diálogo de Cor (Para fechar o requisito do Item 5)
            color = QColorDialog.getColor(current_color, self, "Cor do Texto")
            
            # Aplicamos a todos os itens selecionados (Suporte a multi-seleção)
            for item in sel:
                # Se for um Nó (StyledNode)
                if hasattr(item, 'text_item'):
                    item.text_item.setFont(font)
                    if color.isValid():
                        item.text_item.setDefaultTextColor(color)
                    # Força o ajuste do tamanho do nó caso o texto tenha crescido
                    if hasattr(item, 'center_text'):
                        item.center_text()
                
                # Se for uma Legenda de Conexão (ConnectionLabel)
                elif isinstance(item, ConnectionLabel):
                    item.setFont(font)
                    if color.isValid():
                        item.setDefaultTextColor(color)

    def change_node_color(self):
        sel = self.scene.selectedItems()
        if not sel: return
        color = QColorDialog.getColor(Qt.GlobalColor.yellow, self, "Cor do Objeto")
        if color.isValid():
            for item in sel:
                if hasattr(item, 'set_custom_color'):
                    item.set_custom_color(color)

    def apply_node_shadow(self):
        """ITEM 12: Liga e desliga a sombra corretamente"""
        for item in self.scene.selectedItems():
            if hasattr(item, 'toggle_shadow'):
                item.toggle_shadow()

    def on_selection_changed(self):
        sel = self.scene.selectedItems()
        if len(sel) == 1 and hasattr(sel[0], 'rect'):
            item = sel[0]
            self.in_x.setText(str(int(item.pos().x()))); self.in_y.setText(str(int(item.pos().y())))
            self.in_w.setText(str(int(item.rect().width()))); self.in_h.setText(str(int(item.rect().height())))

    def apply_status_changes(self):
        sel = self.scene.selectedItems()
        if len(sel) == 1:
            try:
                item = sel[0]; item.setPos(float(self.in_x.text()), float(self.in_y.text()))
                item.setRect(0, 0, float(self.in_w.text()), float(self.in_h.text()))
            except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv); window = AmareloMainWindow(); window.show(); sys.exit(app.exec())