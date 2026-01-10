import sys
import os
from PySide6.QtWidgets import (QMainWindow, QApplication, QGraphicsView, 
                             QGraphicsScene, QFileDialog, QToolBar,
                             QStatusBar, QWidget, QHBoxLayout, QLineEdit, 
                             QLabel, QFrame, QStyle, QComboBox)
from PySide6.QtCore import Qt, QRectF, QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QImage, QIcon, QAction, QWheelEvent, QKeyEvent, QUndoStack
from core.icon_manager import IconManager
from items.connection_label import ConnectionLabel # Se quiser usar labels automáticos
from items.group_box import GroupBox

# Imports das lógicas que criamos nos arquivos separados
from core.text_editor import TextEditorManager
from core.style_manager import StyleManager

# Imports internos de itens e persistência
try:
    from items.shapes import StyledNode as MindMapNode
    from core.connection import SmartConnection
    from core.persistence import PersistenceManager
except ImportError as e:
    print(f"Erro de importação: {e}")
    MindMapNode = None
    SmartConnection = None
    PersistenceManager = None

class InfiniteCanvas(QGraphicsView):
    """Área de trabalho com Zoom e Pan"""
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setBackgroundBrush(QColor("#f5f0e9"))
        self.setFrameStyle(QFrame.NoFrame)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
    def wheelEvent(self, event: QWheelEvent):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if not self.itemAt(event.pos()):
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setDragMode(QGraphicsView.RubberBandDrag)
        super().mouseReleaseEvent(event)

class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amarelo Mind")
        self.showMaximized()
        
        # Inicializa a pilha de desfazer
        self.undo_stack = QUndoStack(self)
        
        # Design da interface (QSS)
        self.setStyleSheet("""
            QMainWindow { background-color: #2d2d2d; }
            QToolBar { background-color: #1a1a1a; border-bottom: 2px solid #f2f71d; padding: 5px; }
            QStatusBar { background-color: #1a1a1a; color: #f2f71d; border-top: 1px solid #f2f71d; }
            QLabel { color: #f5f0e9; font-size: 10px; }
            QLineEdit { background-color: #3d3d3d; color: #f2f71d; border: 1px solid #555; border-radius: 4px; padding: 2px; }
        """)

        # Configuração da Cena e View
        self.scene = QGraphicsScene(-10**6, -10**6, 2*10**6, 2*10**6)
        self.view = InfiniteCanvas(self.scene, self)
        self.setCentralWidget(self.view)

        if PersistenceManager:
            self.persistence = PersistenceManager(self.scene)

        # Monta a UI
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Conecta evento de seleção para atualizar a barra de status
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def setup_toolbar(self):
        """Configura todos os botões da barra de ferramentas"""
        self.toolbar = QToolBar("Menu Principal")
        self.toolbar.setIconSize(QSize(28, 28))
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # 1-5: Arquivo e Edição Básica
        self.add_btn(QStyle.StandardPixmap.SP_FileIcon, "Novo", self.new_project, "Ctrl+N")
        self.add_btn(QStyle.StandardPixmap.SP_DialogOpenButton, "Abrir", self.open_project, "Ctrl+O")
        self.add_btn(QStyle.StandardPixmap.SP_DialogSaveButton, "Salvar", self.save_project, "Ctrl+S")
        self.add_btn(QStyle.StandardPixmap.SP_ArrowBack, "Desfazer", self.undo, "Ctrl+Z")
        self.add_btn(QStyle.StandardPixmap.SP_ArrowForward, "Refazer", self.redo, "Ctrl+R")
        self.add_btn(QStyle.StandardPixmap.SP_DialogNoButton, "Agrupar (10)", self.group_selected)
        self.toolbar.addSeparator()

        # 6: Adicionar Nó
        self.obj_combo = QComboBox()
        self.obj_combo.setFixedWidth(50)
        self.obj_combo.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), "")
        self.obj_combo.currentIndexChanged.connect(self.add_node)
        self.toolbar.addWidget(self.obj_combo)

        # 7-11: Manipulação
        self.add_btn(QStyle.StandardPixmap.SP_ArrowRight, "Duplicar", self.duplicate_node, "+")
        self.add_btn(QStyle.StandardPixmap.SP_TrashIcon, "Excluir", self.delete_selected, "Delete")
        self.add_btn(QStyle.StandardPixmap.SP_BrowserReload, "Conectar", self.connect_nodes, "L")
        self.add_btn(QStyle.StandardPixmap.SP_DialogApplyButton, "Exportar PNG", self.export_project, "Ctrl+E")

        # --- Botões 12 e 13 ---
        self.toolbar.addSeparator()
        self.add_btn(QStyle.StandardPixmap.SP_FileDialogContentsView, "Ícone (12)", self.add_icon_to_node)
        self.add_btn(QStyle.StandardPixmap.SP_DialogNoButton, "Legenda Linha (13)", self.add_line_label)
        
        # --- Botão 14: Formatação de Texto ---
        self.toolbar.addSeparator()
        self.add_btn(QStyle.StandardPixmap.SP_TitleBarMenuButton, "Negrito", self.set_bold, "Ctrl+B")
        self.add_btn(QStyle.StandardPixmap.SP_FileDialogDetailedView, "Fonte", self.choose_font)

        # --- Botão 15: Estética do Objeto ---
        self.toolbar.addSeparator()
        self.add_btn(QStyle.StandardPixmap.SP_DialogResetButton, "Cor de Fundo", self.change_node_color)
        self.add_btn(QStyle.StandardPixmap.SP_MessageBoxQuestion, "Sombra", self.apply_node_shadow)

    def add_btn(self, style_pixmap, tooltip, callback, shortcut=None):
        icon = self.style().standardIcon(style_pixmap)
        action = QAction(icon, "", self)
        action.setToolTip(tooltip)
        if shortcut: action.setShortcut(shortcut)
        action.triggered.connect(callback)
        self.toolbar.addAction(action)

    def setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        container = QWidget()
        layout = QHBoxLayout(container)
        self.in_x = QLineEdit(); self.in_y = QLineEdit()
        self.in_w = QLineEdit(); self.in_h = QLineEdit()
        for label, edit in zip(["X:", "Y:", "W:", "H:"], [self.in_x, self.in_y, self.in_w, self.in_h]):
            layout.addWidget(QLabel(label)); edit.setFixedWidth(60)
            edit.returnPressed.connect(self.apply_status_changes); layout.addWidget(edit)
        self.status.addPermanentWidget(container)

    # --- Lógicas de Ação ---
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
            center = self.view.mapToScene(self.view.viewport().rect().center())
            node = MindMapNode(center.x() - 75, center.y() - 40)
            self.scene.addItem(node)

    def duplicate_node(self):
        sel = self.scene.selectedItems()
        if len(sel) == 1:
            old = sel[0]
            new_node = MindMapNode(old.pos().x() + old.rect().width() + 20, old.pos().y())
            self.scene.addItem(new_node)

    def delete_selected(self):
        for item in self.scene.selectedItems(): self.scene.removeItem(item)

    def connect_nodes(self):
        sel = self.scene.selectedItems()
        if len(sel) >= 2 and SmartConnection:
            for i in range(len(sel)-1):
                conn = SmartConnection(sel[i], sel[i+1])
                self.scene.addItem(conn)

    def export_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar", "", "PNG (*.png)")
        if path:
            rect = self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
            img = QImage(rect.size().toSize(), QImage.Format_ARGB32)
            img.fill(Qt.GlobalColor.white)
            painter = QPainter(img)
            self.scene.render(painter, QRectF(img.rect()), rect)
            painter.end()
            img.save(path)

    # --- Lógicas de Texto (Botão 14) ---
    def set_bold(self):
        sel = self.scene.selectedItems()
        if sel and hasattr(sel[0], 'text_item'):
            is_bold = sel[0].text_item.font().bold()
            TextEditorManager.format_selection(sel[0].text_item, bold=not is_bold)

    def choose_font(self):
        sel = self.scene.selectedItems()
        if sel and hasattr(sel[0], 'text_item'):
            TextEditorManager.open_font_dialog(self, sel[0].text_item)

    # --- Lógicas de Estética (Botão 15) ---
    def change_node_color(self):
        sel = self.scene.selectedItems()
        if sel: StyleManager.change_background_color(self, sel[0])

    def apply_node_shadow(self):
        sel = self.scene.selectedItems()
        for item in sel: StyleManager.apply_shadow(item)

    # --- Eventos de Interface ---
    def on_selection_changed(self):
        sel = self.scene.selectedItems()
        if len(sel) == 1 and hasattr(sel[0], 'rect'):
            item = sel[0]
            self.in_x.setText(str(int(item.pos().x())))
            self.in_y.setText(str(int(item.pos().y())))
            self.in_w.setText(str(int(item.rect().width())))
            self.in_h.setText(str(int(item.rect().height())))

    def apply_status_changes(self):
        sel = self.scene.selectedItems()
        if len(sel) == 1:
            try:
                item = sel[0]
                item.setPos(float(self.in_x.text()), float(self.in_y.text()))
                item.setRect(0, 0, float(self.in_w.text()), float(self.in_h.text()))
                if hasattr(item, 'update_handle_positions'): item.update_handle_positions()
            except: pass
    

    def add_icon_to_node(self):
        sel = self.scene.selectedItems()
        if sel and hasattr(sel[0], 'text_item'):
            IconManager.open_emoji_picker(self, sel[0])

    def add_line_label(self):
        sel = self.scene.selectedItems()
        # Se o usuário selecionou uma conexão (SmartConnection)
        from core.connection import SmartConnection
        for item in sel:
            if isinstance(item, SmartConnection):
                label = ConnectionLabel("Link", item)
                label.update_position()
                # Precisamos garantir que a conexão atualize a posição da label ao mover
                item.label = label
    
    def group_selected(self):
        items = self.scene.selectedItems()
        if not items: return
        
        # Calcula a área que abrange todos os itens selecionados
        rect = items[0].sceneBoundingRect()
        for item in items:
            rect = rect.united(item.sceneBoundingRect())
            
        # Adiciona uma margem de respiro
        rect.adjust(-20, -20, 20, 20)
        
        group = GroupBox(rect)
        self.scene.addItem(group)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AmareloMainWindow()
    window.show()
    sys.exit(app.exec())