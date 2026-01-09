import sys, os
from PySide6.QtWidgets import (QMainWindow, QApplication, QGraphicsView, 
                             QGraphicsScene, QFileDialog, QToolBar,
                             QStatusBar, QWidget, QHBoxLayout, QLineEdit, QLabel)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QImage

# Importações dos seus módulos internos
try:
    from items.shapes import StyledNode as MindMapNode
    from core.connection import SmartConnection
except ImportError as e:
    print(f"Atenção: Erro ao importar módulos internos: {e}")
    MindMapNode = None
    SmartConnection = None

class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amarelo Mind")
        self.resize(1100, 700)

        # 1. Configuração da Cena e Visão
        self.scene = QGraphicsScene(-5000, -5000, 10000, 10000)
        self.view = QGraphicsView(self.scene)
        
        self.view.setRenderHints(
            QPainter.Antialiasing | 
            QPainter.SmoothPixmapTransform
        )

        self.view.setBackgroundBrush(QColor("#f5f0e9"))
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setCentralWidget(self.view)

        # 2. Interface e Conexões
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Conecta o evento de seleção para atualizar a barra de status
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def setup_toolbar(self):
        tb = self.addToolBar("Ferramentas")
        
        btn_node = tb.addAction("Add Nó")
        btn_node.triggered.connect(self.add_node)
        
        btn_conn = tb.addAction("Conectar")
        btn_conn.triggered.connect(self.connect_nodes)
        
        btn_media = tb.addAction("Mídia")
        btn_media.triggered.connect(self.add_media)
        
        btn_exp = tb.addAction("Exportar")
        btn_exp.triggered.connect(self.export_map)

    def setup_statusbar(self):
        """Módulo de Controle Numérico"""
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.setStyleSheet("background-color: #2b2b2b; color: #f5f0e9; border-top: 1px solid #c3c910;")

        self.status_container = QWidget()
        layout = QHBoxLayout(self.status_container)
        layout.setContentsMargins(10, 0, 10, 0)

        # Campos de input para X, Y, Largura e Altura
        self.input_x = QLineEdit(); self.input_y = QLineEdit()
        self.input_w = QLineEdit(); self.input_h = QLineEdit()
        
        self.inputs = {"X:": self.input_x, "Y:": self.input_y, "L:": self.input_w, "A:": self.input_h}
        style = "background: #3d3d3d; color: #f2f71d; border: 1px solid #818511; border-radius: 3px;"

        for label_text, widget in self.inputs.items():
            layout.addWidget(QLabel(label_text))
            widget.setFixedWidth(50)
            widget.setStyleSheet(style)
            widget.returnPressed.connect(self.update_object_from_status)
            layout.addWidget(widget)

        self.status.addPermanentWidget(self.status_container)

    def on_selection_changed(self):
        """Atualiza a barra de status quando um nó é clicado"""
        selected = self.scene.selectedItems()
        if len(selected) == 1 and hasattr(selected[0], 'rect'):
            item = selected[0]
            self.input_x.setText(str(int(item.pos().x())))
            self.input_y.setText(str(int(item.pos().y())))
            self.input_w.setText(str(int(item.rect().width())))
            self.input_h.setText(str(int(item.rect().height())))
        else:
            for widget in self.inputs.values():
                widget.clear()

    def update_object_from_status(self):
        """Aplica os valores digitados na barra ao objeto"""
        selected = self.scene.selectedItems()
        if len(selected) == 1:
            item = selected[0]
            try:
                item.setPos(float(self.input_x.text()), float(self.input_y.text()))
                item.setRect(0, 0, float(self.input_w.text()), float(self.input_h.text()))
                if hasattr(item, 'update_handle_positions'):
                    item.update_handle_positions()
            except ValueError:
                self.status.showMessage("Erro: Use apenas números", 2000)

    def add_node(self):
        if MindMapNode:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            node = MindMapNode(center.x(), center.y())
            self.scene.addItem(node)

    def connect_nodes(self):
        sel = self.scene.selectedItems()
        if len(sel) == 2 and SmartConnection:
            conn = SmartConnection(sel[0], sel[1])
            self.scene.addItem(conn)

    def add_media(self):
        sel = self.scene.selectedItems()
        if sel and hasattr(sel[0], 'set_image'):
            path, _ = QFileDialog.getOpenFileName(self, "Imagem", "", "Images (*.png *.jpg)")
            if path: 
                sel[0].set_image(path)

    def export_map(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar", "", "PNG (*.png)")
        if path:
            rect = self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
            img = QImage(rect.size().toSize(), QImage.Format_ARGB32)
            img.fill(Qt.white)
            
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter, QRectF(img.rect()), rect)
            painter.end()
            img.save(path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AmareloMainWindow()
    window.show()
    sys.exit(app.exec())