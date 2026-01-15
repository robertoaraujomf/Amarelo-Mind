import sys
import os
import json
from PySide6.QtWidgets import (QMainWindow, QApplication, QGraphicsView, 
                             QGraphicsScene, QFileDialog, QToolBar,
                             QStatusBar, QWidget, QFrame, QStyle, 
                             QFontDialog, QColorDialog, QGraphicsDropShadowEffect,
                             QCheckBox)
from PySide6.QtCore import Qt, QRectF, QSize, QPointF, QPoint
from PySide6.QtGui import (QPainter, QColor, QImage, QIcon, QAction, QLinearGradient,
                          QWheelEvent, QKeyEvent, QUndoStack, QPen, QFont, QPixmap, QBrush)

# --- CLASSES DO SISTEMA ---
try:
    from items.shapes import StyledNode as MindMapNode 
    from core.connection import SmartConnection
except ImportError:
    # Placeholder funcional para garantir execução
    from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
    class MindMapNode(QGraphicsRectItem):
        def __init__(self, x, y, brush=None):
            super().__init__(0, 0, 160, 60)
            self.setPos(x, y)
            self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemSendsGeometryChanges)
            # Aplicar Degradê Amarelo Padrão
            if not brush:
                grad = QLinearGradient(0, 0, 0, 60)
                grad.setColorAt(0, QColor("#fdfc47"))
                grad.setColorAt(1, QColor("#24fe41")) # Exemplo de degradê, ajuste para amarelo
                self.setBrush(QBrush(QColor("#f2f71d")))
            else:
                self.setBrush(brush)
            
            self.text_item = QGraphicsTextItem("", self)
            self.text_item.setPos(10, 15)
            self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)

class InfiniteCanvas(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QColor("#ece6e6")) # 9. Background atualizado
        self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._is_panning = False

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if event.button() == Qt.RightButton and not item:
            self._is_panning = True
            self.setCursor(Qt.ClosedHandCursor)
            self._last_pan_pos = event.position().toPoint()
            return
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag if item else QGraphicsView.RubberBandDrag)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.position().toPoint() - self._last_pan_pos
            self._last_pan_pos = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_panning = False
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amarelo Mind")
        self.undo_stack = QUndoStack(self)
        self.current_file = None
        
        self.setStyleSheet("""
            QMainWindow { background-color: #ece6e6; }
            QToolBar { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #444, stop:1 #222);
                border-bottom: 1px solid #111; color: white; spacing: 10px;
            }
        """)

        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.view = InfiniteCanvas(self.scene, self)
        self.setCentralWidget(self.view)
        
        self.setup_toolbar()
        self.showMaximized()

    # --- DESENHO DE ÍCONES ---

    def draw_font_icon(self):
        pixmap = QPixmap(100, 100); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setPen(Qt.white); p.setFont(QFont("Arial", 70, QFont.Bold))
        p.drawText(pixmap.rect(), Qt.AlignCenter, "F")
        p.end(); return QIcon(pixmap)

    def draw_shadow_ball_icon(self):
        pixmap = QPixmap(100, 100); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(0,0,0,100)); p.setPen(Qt.transparent)
        p.drawEllipse(20, 70, 60, 15) # Sombra no chão
        grad = QLinearGradient(30, 20, 70, 60)
        grad.setColorAt(0, Qt.white); grad.setColorAt(1, QColor("#f2f71d"))
        p.setBrush(grad); p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(25, 15, 50, 50) # Bola 3D
        p.end(); return QIcon(pixmap)

    def setup_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(40, 40))
        self.addToolBar(self.toolbar)

        # Ações de Arquivo
        self.toolbar.addAction(QAction(self.style().standardIcon(QStyle.SP_DialogOpenButton), "Abrir", self, triggered=self.open_project))
        act_save = QAction(self.style().standardIcon(QStyle.SP_DriveHDIcon), "Salvar", self, triggered=self.save_project)
        act_save.setShortcut("Ctrl+S")
        self.toolbar.addAction(act_save)

        self.toolbar.addSeparator()

        # Magnetismo
        self.cb_magnetismo = QCheckBox("Magnetismo (M)")
        self.cb_magnetismo.setStyleSheet("color: white;")
        self.toolbar.addWidget(self.cb_magnetismo)

        self.toolbar.addSeparator()

        # Undo/Redo
        self.act_undo = self.undo_stack.createUndoAction(self, "Desfazer")
        self.act_undo.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.act_undo.setShortcut("Ctrl+Z")
        self.toolbar.addAction(self.act_undo)

        self.act_redo = self.undo_stack.createRedoAction(self, "Refazer")
        self.act_redo.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.act_redo.setShortcut("Ctrl+R")
        self.toolbar.addAction(self.act_redo)

        self.toolbar.addSeparator()

        # Criação
        self.toolbar.addAction(QAction(self.style().standardIcon(QStyle.SP_FileIcon), "Adicionar Objeto (N)", self, triggered=self.add_smart_node, shortcut="N"))
        self.toolbar.addAction(QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Conectar (C)", self, triggered=self.connect_nodes, shortcut="C"))
        self.toolbar.addAction(QAction(self.draw_font_icon(), "Fonte", self, triggered=self.unified_font))
        self.toolbar.addAction(QAction(self.style().standardIcon(QStyle.SP_DialogResetButton), "Cor", self, triggered=self.apply_color))
        self.toolbar.addAction(QAction(self.draw_shadow_ball_icon(), "Sombra", self, triggered=self.toggle_shadow))
        self.toolbar.addAction(QAction(self.style().standardIcon(QStyle.SP_TrashIcon), "Excluir", self, triggered=self.delete_sel, shortcut="Delete"))

    # --- LÓGICA DE FUNCIONAMENTO ---

    def add_smart_node(self):
        sel = self.scene.selectedItems()
        new_brush = None
        if len(sel) == 1 and isinstance(sel[0], MindMapNode):
            new_brush = sel[0].brush() # Copia o degradê/cor do selecionado
            pos = sel[0].pos() + QPointF(40, 40)
        else:
            pos = self.view.mapToScene(self.view.rect().center())

        node = MindMapNode(pos.x(), pos.y(), brush=new_brush)
        self.scene.addItem(node)
        
        # Foco automático no texto
        node.setSelected(True)
        node.text_item.setFocus()
        # Seleciona todo o texto para facilitar a substituição
        cursor = node.text_item.textCursor()
        cursor.select(cursor.SelectionType.Document)
        node.text_item.setTextCursor(cursor)

    def save_project(self):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(self, "Salvar Como", "", "Amarelo (*.amarelo)")
            if not path: return
            self.current_file = path
        
        data = [{"pos": [i.x(), i.y()], "text": i.text_item.toPlainText(), "color": i.brush().color().name()} 
                for i in self.scene.items() if isinstance(i, MindMapNode)]
        with open(self.current_file, 'w') as f: json.dump(data, f)
        self.statusBar().showMessage(f"Salvo: {self.current_file}")

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Amarelo (*.amarelo)")
        if path:
            self.scene.clear()
            self.current_file = path
            with open(path, 'r') as f:
                for n in json.load(f):
                    node = MindMapNode(n["pos"][0], n["pos"][1])
                    node.text_item.setPlainText(n["text"])
                    node.setBrush(QBrush(QColor(n["color"])))
                    self.scene.addItem(node)

    def keyPressEvent(self, event):
        # ESC para des-selecionar
        if event.key() == Qt.Key_Escape:
            self.scene.clearSelection()
        # M para Magnetismo
        elif event.key() == Qt.Key_M:
            self.cb_magnetismo.setChecked(not self.cb_magnetismo.isChecked())
        super().keyPressEvent(event)

    def unified_font(self):
        sel = self.scene.selectedItems()
        if not sel: return
        ok, font = QFontDialog.getFont(self)
        if ok:
            color = QColorDialog.getColor(Qt.black, self, "Cor da Fonte")
            for item in sel:
                if hasattr(item, 'text_item'):
                    item.text_item.setFont(font)
                    if color.isValid(): item.text_item.setDefaultTextColor(color)

    def apply_color(self):
        sel = self.scene.selectedItems()
        if not sel: return
        color = QColorDialog.getColor(Qt.yellow, self)
        if color.isValid():
            for item in sel:
                if isinstance(item, MindMapNode):
                    grad = QLinearGradient(0, 0, 0, 60)
                    grad.setColorAt(0, color.lighter(120))
                    grad.setColorAt(1, color.darker(110))
                    item.setBrush(grad)

    def toggle_shadow(self):
        for item in self.scene.selectedItems():
            if item.graphicsEffect(): item.setGraphicsEffect(None)
            else:
                s = QGraphicsDropShadowEffect(); s.setBlurRadius(15); s.setOffset(5, 5)
                item.setGraphicsEffect(s)
        self.view.viewport().update()

    def connect_nodes(self):
        sel = self.scene.selectedItems()
        if len(sel) >= 2:
            try:
                conn = SmartConnection(sel[0], sel[1])
                self.scene.addItem(conn)
            except: pass

    def delete_sel(self):
        for i in self.scene.selectedItems(): self.scene.removeItem(i)

if __name__ == "__main__":
    app = QApplication(sys.argv); win = AmareloMainWindow(); win.show(); sys.exit(app.exec())