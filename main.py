import sys
import os
import json
from PySide6.QtWidgets import (QMainWindow, QApplication, QGraphicsView, 
                             QGraphicsScene, QFileDialog, QToolBar,
                             QStatusBar, QWidget, QFrame, QStyle, 
                             QFontDialog, QColorDialog, QGraphicsDropShadowEffect,
                             QCheckBox, QPushButton, QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, QRectF, QSize, QPointF, QPoint, QMimeData, QUrl
from PySide6.QtGui import (QPainter, QColor, QImage, QIcon, QAction, QLinearGradient,
                          QWheelEvent, QKeyEvent, QUndoStack, QPen, QFont, QPixmap, QBrush,
                          QClipboard, QTextCharFormat, QTextDocument)

# --- ÍCONES: sempre a partir da pasta do main.py ---
_MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    from core.icon_manager import IconManager
    IconManager.set_icons_base(_MAIN_DIR)
except Exception:
    pass

# --- CLASSES DO SISTEMA ---
try:
    from items.shapes import StyledNode as MindMapNode 
    from core.connection import SmartConnection
    from items.group_item import GroupNode
except ImportError:
    # Placeholder funcional para garantir execução
    from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
    class MindMapNode(QGraphicsRectItem):
        def __init__(self, x, y, brush=None):
            super().__init__(0, 0, 160, 60)
            self.setPos(x, y)
            self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemSendsGeometryChanges)
            if not brush:
                grad = QLinearGradient(0, 0, 0, 60)
                grad.setColorAt(0, QColor("#fdfc47"))
                grad.setColorAt(1, QColor("#ffd700"))
                self.setBrush(QBrush(grad))
            else:
                self.setBrush(brush)
            self.text_item = QGraphicsTextItem("", self)
            self.text_item.setPos(10, 15)
            self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)

class InfiniteCanvas(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QColor("#ece6e6"))
        self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._is_panning = False
        self._last_pan_pos = None
        # Seleção por área retangular: itens que intersectam o retângulo são selecionados
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        # Pan apenas com botão direito em área vazia
        if event.button() == Qt.RightButton and not item:
            self._is_panning = True
            self.setCursor(Qt.ClosedHandCursor)
            self._last_pan_pos = event.position().toPoint()
            return
        if event.button() == Qt.LeftButton:
            # Shift+Click para seleção múltipla
            if event.modifiers() & Qt.ShiftModifier and item:
                item.setSelected(not item.isSelected())
            else:
                # Clique em item: arrasta. Clique em área vazia: seleção por retângulo (rubber band)
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

    def keyPressEvent(self, event):
        # Navegação com setas quando nada está selecionado
        if not self.scene().selectedItems():
            step = 20
            if event.key() == Qt.Key_Left:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - step)
            elif event.key() == Qt.Key_Right:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + step)
            elif event.key() == Qt.Key_Up:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - step)
            elif event.key() == Qt.Key_Down:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() + step)
        super().keyPressEvent(event)

class AmareloMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amarelo Mind")
        self.undo_stack = QUndoStack(self)
        self.current_file = None
        self.clipboard_content = ""  # Para copiar/colar conteúdo
        self.groups = []  # Lista de grupos
        
        # Estilo moderno com gradientes e profundidade
        self.setStyleSheet("""
            QMainWindow { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f5f5f5, stop:1 #ece6e6); 
            }
            QToolBar { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #2a2a2a);
                border: none;
                border-bottom: 2px solid #1a1a1a;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #3a3a3a);
                border: none;
                border-radius: 4px;
                padding: 5px;
                min-width: 40px;
                min-height: 40px;
            }
            QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a6a6a, stop:1 #4a4a4a);
            }
            QToolButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3a, stop:1 #2a2a2a);
            }
            QToolButton:disabled {
                background: #2a2a2a;
                opacity: 0.5;
            }
            QCheckBox {
                color: white;
                padding: 5px;
            }
        """)

        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.view = InfiniteCanvas(self.scene, self)
        self.setCentralWidget(self.view)
        
        # Conecta seleção para atualizar botões
        self.scene.selectionChanged.connect(self.update_button_states)
        
        self.setup_toolbar()
        self.update_button_states()
        self.showMaximized()

    def setup_toolbar(self):
        """Configura a barra de ferramentas com todos os botões conforme especificação"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(40, 40))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)  # Apenas ícones
        self.addToolBar(self.toolbar)

        # Botão Novo (Ctrl+N)
        act_new = QAction(IconManager.load_icon("Novo.png", "N"), "New mind map", self)
        act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self.new_window)
        self.toolbar.addAction(act_new)

        # Botão Abrir (Ctrl+A)
        act_open = QAction(IconManager.load_icon("Abrir.png", "O"), "Open mind map", self)
        act_open.setShortcut("Ctrl+A")
        act_open.triggered.connect(self.open_project)
        self.toolbar.addAction(act_open)

        # Botão Salvar (Ctrl+S)
        act_save = QAction(IconManager.load_icon("Salvar.png", "S"), "Save changes or save as", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save_project)
        self.toolbar.addAction(act_save)

        # Botão Exportar PNG
        self.act_export = QAction(IconManager.load_icon("Exportar.png", "E"), "Export as image", self)
        self.act_export.triggered.connect(self.export_png)
        self.toolbar.addAction(self.act_export)

        self.toolbar.addSeparator()

        # Botão Desfazer (Ctrl+Z)
        self.act_undo = self.undo_stack.createUndoAction(self, "Undo")
        self.act_undo.setIcon(IconManager.load_icon("Desfazer.png", "U"))
        self.act_undo.setShortcut("Ctrl+Z")
        self.toolbar.addAction(self.act_undo)

        # Botão Refazer (Ctrl+R)
        self.act_redo = self.undo_stack.createRedoAction(self, "Redo")
        self.act_redo.setIcon(IconManager.load_icon("Refazer.png", "R"))
        self.act_redo.setShortcut("Ctrl+R")
        self.toolbar.addAction(self.act_redo)

        self.toolbar.addSeparator()

        # Botão Copiar (Ctrl+C)
        act_copy = QAction(IconManager.load_icon("Copiar.png", "C"), "Copy", self)
        act_copy.setShortcut("Ctrl+C")
        act_copy.triggered.connect(self.copy_content)
        self.toolbar.addAction(act_copy)

        # Botão Colar (Ctrl+V)
        act_paste = QAction(IconManager.load_icon("Colar.png", "V"), "Paste", self)
        act_paste.setShortcut("Ctrl+V")
        act_paste.triggered.connect(self.paste_content)
        self.toolbar.addAction(act_paste)

        self.toolbar.addSeparator()

        # Botão Adicionar Objeto (+)
        act_add = QAction(IconManager.load_icon("Adicionar.png", "+"), "Add Object", self)
        act_add.setShortcut("+")
        act_add.triggered.connect(self.add_smart_node)
        self.toolbar.addAction(act_add)

        # Botão Agrupar
        self.act_group = QAction(IconManager.load_icon("Agrupar.png", "G"), "Group", self)
        self.act_group.triggered.connect(self.toggle_group)
        self.toolbar.addAction(self.act_group)

        # Botão Conectar (C)
        act_connect = QAction(IconManager.load_icon("Conectar.png", "C"), "Connect", self)
        act_connect.setShortcut("C")
        act_connect.triggered.connect(self.connect_nodes)
        self.toolbar.addAction(act_connect)

        # Botão Excluir (Delete)
        act_delete = QAction(IconManager.load_icon("Excluir.png", "D"), "Delete", self)
        act_delete.setShortcut("Delete")
        act_delete.triggered.connect(self.delete_sel)
        self.toolbar.addAction(act_delete)

        self.toolbar.addSeparator()

        # Botão Mídia
        self.act_media = QAction(IconManager.load_icon("Midia.png", "M"), "Media", self)
        self.act_media.triggered.connect(self.add_media)
        self.toolbar.addAction(self.act_media)

        # Botão Fonte
        self.act_font = QAction(IconManager.load_icon("Fonte.png", "F"), "Font", self)
        self.act_font.triggered.connect(self.unified_font)
        self.toolbar.addAction(self.act_font)

        # Botão Cores
        self.act_colors = QAction(IconManager.load_icon("Cores.png", "C"), "Colors", self)
        self.act_colors.triggered.connect(self.apply_color)
        self.toolbar.addAction(self.act_colors)

        # Botão Sombra
        self.act_shadow = QAction(IconManager.load_icon("Sombra.png", "S"), "Shadow", self)
        self.act_shadow.triggered.connect(self.toggle_shadow)
        self.toolbar.addAction(self.act_shadow)

        # Botão Magnetismo (= Alinhar): um único botão, ícone Alinhar.png (assets/icons)
        self.cb_magnetismo = QCheckBox()
        self.cb_magnetismo.setChecked(True)  # Habilitado por padrão (como Alinhar)
        self.cb_magnetismo.setToolTip("Magnetismo / Alinhar (M)")
        self.cb_magnetismo.setStyleSheet("""
            QCheckBox::indicator {
                width: 40px;
                height: 40px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #3a3a3a);
                border: none;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f2f71d, stop:1 #ffd700);
            }
        """)
        alinhar_path = os.path.normpath(os.path.join(_MAIN_DIR, "assets", "icons", "Alinhar.png"))
        icon_magnetismo = QIcon()
        if os.path.isfile(alinhar_path):
            icon_magnetismo.addFile(alinhar_path)
            icon_magnetismo.addFile(alinhar_path, QSize(40, 40))
        else:
            icon_magnetismo = IconManager.load_icon("Alinhar.png", "M")
        act_magnetismo = QAction(icon_magnetismo, "Magnetismo / Alinhar (M)", self)
        act_magnetismo.setCheckable(True)
        act_magnetismo.setChecked(True)
        act_magnetismo.triggered.connect(lambda checked: self.cb_magnetismo.setChecked(checked))
        self.cb_magnetismo.toggled.connect(lambda checked: act_magnetismo.setChecked(checked))
        self.toolbar.addAction(act_magnetismo)

    def update_button_states(self):
        """Atualiza estados dos botões baseado na seleção"""
        has_selection = len(self.scene.selectedItems()) > 0
        has_content = len([i for i in self.scene.items() if isinstance(i, MindMapNode)]) > 0
        
        # Botões que requerem seleção
        self.act_font.setEnabled(has_selection)
        self.act_colors.setEnabled(has_selection)
        self.act_shadow.setEnabled(has_selection)
        self.act_group.setEnabled(has_selection and len(self.scene.selectedItems()) > 1)
        self.act_media.setEnabled(has_selection)
        
        # Exportar desabilitado quando vazio
        self.act_export.setEnabled(has_content)

    def new_window(self):
        """Abre nova janela com canvas vazio"""
        new_win = AmareloMainWindow()
        new_win.show()

    def add_smart_node(self):
        """Adiciona novo objeto ou duplica se um estiver selecionado"""
        sel = self.scene.selectedItems()
        
        # Se há seleção e pressionou + ou clicou no botão, duplica
        if len(sel) == 1 and isinstance(sel[0], MindMapNode):
            # Duplica preservando background e sombra, mas descartando conteúdo
            original = sel[0]
            new_brush = original.brush()
            shadow = original.graphicsEffect()
            if shadow:
                from PySide6.QtWidgets import QGraphicsDropShadowEffect
                new_shadow = QGraphicsDropShadowEffect()
                new_shadow.setBlurRadius(shadow.blurRadius())
                new_shadow.setOffset(shadow.xOffset(), shadow.yOffset())
                new_shadow.setColor(shadow.color())
            else:
                new_shadow = None
            
            pos = original.pos() + QPointF(40, 40)
            node = MindMapNode(pos.x(), pos.y(), brush=new_brush, shadow=new_shadow)
            node.text_item.setPlainText("")  # Conteúdo descartado
        else:
            # Novo objeto
            pos = self.view.mapToScene(self.view.rect().center())
            node = MindMapNode(pos.x(), pos.y())

        self.scene.addItem(node)
        node.setSelected(True)
        node.text_item.setFocus()
        cursor = node.text_item.textCursor()
        cursor.select(cursor.SelectionType.Document)
        node.text_item.setTextCursor(cursor)
        self.update_button_states()

    def save_project(self):
        """Salva ou salva como"""
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(self, "Salvar Como", "", "Amarelo Mind (*.amarelo)")
            if not path:
                return
            if not path.endswith(".amarelo"):
                path += ".amarelo"
            self.current_file = path
        
        data = {
            "nodes": [],
            "connections": [],
            "groups": []
        }
        
        for item in self.scene.items():
            if isinstance(item, MindMapNode):
                node_data = {
                    "pos": [item.pos().x(), item.pos().y()],
                    "size": [item.rect().width(), item.rect().height()],
                    "text": item.text_item.toPlainText(),
                    "brush": item.brush().color().name() if isinstance(item.brush(), QBrush) and not isinstance(item.brush().gradient(), type(None)) else None,
                    "has_shadow": item.graphicsEffect() is not None
                }
                data["nodes"].append(node_data)
            elif isinstance(item, SmartConnection):
                # Salva conexões por índice (simplificado)
                try:
                    nodes = [i for i in self.scene.items() if isinstance(i, MindMapNode)]
                    source_idx = nodes.index(item.source) if item.source in nodes else -1
                    target_idx = nodes.index(item.target) if item.target in nodes else -1
                    if source_idx >= 0 and target_idx >= 0:
                        data["connections"].append({"source": source_idx, "target": target_idx})
                except:
                    pass
        
        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"Salvo: {self.current_file}", 3000)

    def open_project(self):
        """Abre arquivo de mind map"""
        path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Amarelo Mind (*.amarelo)")
        if path:
            self.scene.clear()
            self.current_file = path
            self.groups = []
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                nodes = []
                for n in data.get("nodes", []):
                    node = MindMapNode(n["pos"][0], n["pos"][1])
                    if "size" in n:
                        node.setRect(0, 0, n["size"][0], n["size"][1])
                    node.text_item.setPlainText(n.get("text", ""))
                    if n.get("has_shadow"):
                        shadow = QGraphicsDropShadowEffect()
                        shadow.setBlurRadius(15)
                        shadow.setOffset(5, 5)
                        node.setGraphicsEffect(shadow)
                    self.scene.addItem(node)
                    nodes.append(node)
                
                # Reconecta nós
                for conn_data in data.get("connections", []):
                    try:
                        if conn_data["source"] < len(nodes) and conn_data["target"] < len(nodes):
                            conn = SmartConnection(nodes[conn_data["source"]], nodes[conn_data["target"]])
                            self.scene.addItem(conn)
                    except:
                        pass
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao abrir arquivo: {str(e)}")
            
            self.update_button_states()

    def export_png(self):
        """Exporta apenas o conteúdo desenhado como PNG"""
        items = [i for i in self.scene.items() if isinstance(i, (MindMapNode, SmartConnection))]
        if not items:
            return
        
        # Calcula bounding rect de todos os itens
        rect = items[0].sceneBoundingRect()
        for item in items[1:]:
            rect = rect.united(item.sceneBoundingRect())
        
        # Adiciona margem
        rect = rect.adjusted(-20, -20, 20, 20)
        
        # Cria imagem
        img = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(-rect.topLeft())
        
        # Renderiza apenas conexões primeiro (fundo)
        for item in items:
            if isinstance(item, SmartConnection):
                item.paint(painter, None, None)
        
        # Depois renderiza nós
        for item in items:
            if isinstance(item, MindMapNode):
                item.paint(painter, None, None)
        
        painter.end()
        
        # Salva
        path, _ = QFileDialog.getSaveFileName(self, "Exportar PNG", "", "PNG (*.png)")
        if path:
            if not path.endswith(".png"):
                path += ".png"
            img.save(path)
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(f"Exportado: {path}", 3000)

    def copy_content(self):
        """Copia conteúdo dos objetos selecionados (não os objetos)"""
        sel = [i for i in self.scene.selectedItems() if isinstance(i, MindMapNode)]
        if sel:
            texts = [item.text_item.toPlainText() for item in sel]
            self.clipboard_content = "\n".join(texts)
            clipboard = QApplication.clipboard()
            clipboard.setText(self.clipboard_content)

    def paste_content(self):
        """Cola conteúdo nos objetos selecionados"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            text = self.clipboard_content
        
        sel = [i for i in self.scene.selectedItems() if isinstance(i, MindMapNode)]
        if sel and text:
            # Se múltiplos selecionados, cola em cada um
            # Se um só, cola o texto completo
            if len(sel) == 1:
                sel[0].text_item.setPlainText(text)
            else:
                lines = text.split("\n")
                for i, item in enumerate(sel):
                    if i < len(lines):
                        item.text_item.setPlainText(lines[i])

    def toggle_group(self):
        """Agrupa ou desagrupa objetos selecionados"""
        sel = [i for i in self.scene.selectedItems() if isinstance(i, MindMapNode)]
        if len(sel) < 2:
            return
        
        # Verifica se já estão agrupados
        if sel[0].group:
            # Desagrupa
            group = sel[0].group
            for item in group.child_items:
                item.group = None
            self.scene.removeItem(group)
            if group in self.groups:
                self.groups.remove(group)
        else:
            # Agrupa
            group = GroupNode(sel)
            for item in sel:
                item.group = group
            self.scene.addItem(group)
            self.groups.append(group)
        
        self.update_button_states()

    def connect_nodes(self):
        """Conecta objetos selecionados"""
        sel = [i for i in self.scene.selectedItems() if isinstance(i, MindMapNode)]
        if len(sel) >= 2:
            # Conecta todos os pares consecutivos
            for i in range(len(sel) - 1):
                try:
                    conn = SmartConnection(sel[i], sel[i + 1])
                    self.scene.addItem(conn)
                except:
                    pass

    def delete_sel(self):
        """Deleta objetos selecionados e suas conexões"""
        sel = self.scene.selectedItems()
        for item in sel:
            # Remove conexões relacionadas
            if isinstance(item, MindMapNode):
                for conn in self.scene.items():
                    if isinstance(conn, SmartConnection) and (conn.source == item or conn.target == item):
                        self.scene.removeItem(conn)
            self.scene.removeItem(item)
        self.update_button_states()

    def add_media(self):
        """Adiciona mídia (link, imagem, áudio, vídeo) a um objeto"""
        sel = [i for i in self.scene.selectedItems() if isinstance(i, MindMapNode)]
        if not sel:
            return
        
        # Diálogo para escolher tipo de mídia
        media_type, ok = QInputDialog.getItem(
            self, "Adicionar Mídia", "Tipo:",
            ["Link (URL)", "Imagem (Local)", "Imagem (URL)", "Áudio (Local)", "Vídeo (Local)"], 0, False
        )
        
        if not ok:
            return
        
        if "Link" in media_type:
            url, ok = QInputDialog.getText(self, "Adicionar Link", "URL:")
            if ok and url:
                for item in sel:
                    current = item.text_item.toPlainText()
                    item.text_item.setPlainText(f"{current}\n🔗 {url}")
        elif "Imagem (Local)" in media_type:
            path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.gif *.bmp)")
            if path:
                for item in sel:
                    current = item.text_item.toPlainText()
                    item.text_item.setPlainText(f"{current}\n🖼️ {path}")
        elif "Imagem (URL)" in media_type:
            url, ok = QInputDialog.getText(self, "Adicionar Imagem", "URL da Imagem:")
            if ok and url:
                for item in sel:
                    current = item.text_item.toPlainText()
                    item.text_item.setPlainText(f"{current}\n🖼️ {url}")
        elif "Áudio" in media_type:
            path, _ = QFileDialog.getOpenFileName(self, "Selecionar Áudio", "", "Áudio (*.mp3 *.wav *.ogg)")
            if path:
                for item in sel:
                    current = item.text_item.toPlainText()
                    item.text_item.setPlainText(f"{current}\n🎵 {path}")
        elif "Vídeo" in media_type:
            path, _ = QFileDialog.getOpenFileName(self, "Selecionar Vídeo", "", "Vídeo (*.mp4 *.avi *.mov)")
            if path:
                for item in sel:
                    current = item.text_item.toPlainText()
                    item.text_item.setPlainText(f"{current}\n🎬 {path}")

    def unified_font(self):
        """Customiza fonte e estilo dos objetos selecionados"""
        sel = self.scene.selectedItems()
        if not sel:
            return
        
        ok, font = QFontDialog.getFont(self)
        if ok:
            for item in sel:
                if hasattr(item, 'text_item'):
                    item.text_item.setFont(font)
                    # Permite escolher cor da fonte
                    color = QColorDialog.getColor(Qt.black, self, "Cor da Fonte")
                    if color.isValid():
                        item.text_item.setDefaultTextColor(color)

    def apply_color(self):
        """Aplica cor de fundo ou de texto"""
        sel = self.scene.selectedItems()
        if not sel:
            return
        
        # Verifica se há texto selecionado dentro de um objeto
        has_text_selection = False
        for item in sel:
            if hasattr(item, 'text_item'):
                cursor = item.text_item.textCursor()
                if cursor.hasSelection():
                    has_text_selection = True
                    break
        
        if has_text_selection:
            # Muda cor do texto selecionado
            color = QColorDialog.getColor(Qt.black, self, "Cor da Fonte")
            if color.isValid():
                for item in sel:
                    if hasattr(item, 'text_item'):
                        cursor = item.text_item.textCursor()
                        if cursor.hasSelection():
                            fmt = QTextCharFormat()
                            fmt.setForeground(color)
                            cursor.mergeCharFormat(fmt)
        else:
            # Muda cor de fundo do objeto
            color = QColorDialog.getColor(Qt.yellow, self, "Cor de Fundo")
            if color.isValid():
                for item in sel:
                    if isinstance(item, MindMapNode):
                        grad = QLinearGradient(0, 0, 0, item.rect().height())
                        grad.setColorAt(0, color.lighter(120))
                        grad.setColorAt(1, color.darker(110))
                        item.setBrush(QBrush(grad))

    def toggle_shadow(self):
        """Adiciona ou remove sombra lateral"""
        for item in self.scene.selectedItems():
            if isinstance(item, MindMapNode):
                if item.graphicsEffect():
                    item.setGraphicsEffect(None)
                else:
                    shadow = QGraphicsDropShadowEffect()
                    shadow.setBlurRadius(15)
                    shadow.setOffset(5, 5)
                    shadow.setColor(QColor(0, 0, 0, 100))
                    item.setGraphicsEffect(shadow)
        self.view.viewport().update()

    def keyPressEvent(self, event):
        """Manipula teclas de atalho"""
        # ESC para deselecionar
        if event.key() == Qt.Key_Escape:
            self.scene.clearSelection()
            self.update_button_states()
        # M para Magnetismo
        elif event.key() == Qt.Key_M:
            self.cb_magnetismo.setChecked(not self.cb_magnetismo.isChecked())
        # + para adicionar/duplicar (teclado numérico ou Shift+=)
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            if event.modifiers() & Qt.KeypadModifier or (event.key() == Qt.Key_Equal and event.modifiers() & Qt.ShiftModifier):
                self.add_smart_node()
        elif event.key() == Qt.Key_Plus and not (event.modifiers() & (Qt.ControlModifier | Qt.AltModifier)):
            self.add_smart_node()
        # C para conectar
        elif event.key() == Qt.Key_C and not (event.modifiers() & (Qt.ControlModifier | Qt.AltModifier)):
            self.connect_nodes()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Amarelo Mind")
    
    # Tenta carregar o ícone do app
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except:
        base_dir = os.getcwd()
    
    # Tenta diferentes variações do nome do arquivo (case-insensitive)
    icons_dir = os.path.join(base_dir, "assets", "icons")
    if os.path.exists(icons_dir):
        for f in os.listdir(icons_dir):
            if "app" in f.lower() and "icon" in f.lower() and f.lower().endswith(".png"):
                icon_path = os.path.join(icons_dir, f)
                app.setWindowIcon(QIcon(icon_path))
                break
    
    win = AmareloMainWindow()
    win.show()
    sys.exit(app.exec())
