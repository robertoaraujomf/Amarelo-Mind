from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QApplication, QGraphicsDropShadowEffect,
    QGraphicsItem, QGraphicsProxyWidget
)
from PySide6.QtCore import Qt, QRectF, QPointF, QObject, Signal
from PySide6.QtGui import (
    QColor, QBrush, QLinearGradient, QFont, QPen, QPainter
)
from .node_styles import NODE_COLORS, NODE_STATE

MIN_W, MIN_H = 80, 50


class SelectionAwareTextItem(QGraphicsTextItem):
    """QGraphicsTextItem que emite sinais quando há seleção de texto"""
    selectionChanged = Signal(bool)  # True se há seleção, False caso contrário
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_has_selection = False
        # Conectar ao documento para detectar mudanças
        self.document().contentsChanged.connect(self._check_selection)
    
    def _check_selection(self):
        """Verifica se há seleção e emite sinal se mudou"""
        has_sel = self.textCursor().hasSelection()
        if has_sel != self._last_has_selection:
            self._last_has_selection = has_sel
            self.selectionChanged.emit(has_sel)
    
    def mouseMoveEvent(self, event):
        """Detecta movimentos de mouse para seleção de texto"""
        super().mouseMoveEvent(event)
        self._check_selection()
    
    def mouseReleaseEvent(self, event):
        """Detecta liberação do mouse após seleção"""
        super().mouseReleaseEvent(event)
        self._check_selection()
    
    def keyReleaseEvent(self, event):
        """Detecta liberação de tecla para seleção com teclado"""
        super().keyReleaseEvent(event)
        self._check_selection()


class Handle(QGraphicsRectItem):
    """Handle de canto para redimensionamento manual"""
    def __init__(self, parent_node, corner):
        super().__init__(-7, -7, 14, 14, parent_node)
        self.parent_node = parent_node
        self.corner = corner  # 'tl', 'tr', 'bl', 'br'
        self.setBrush(QColor("#f2f71d"))
        self.setPen(QPen(QColor("#1a1a1a"), 1))
        self.setZValue(100)
        self.setCursor(Qt.SizeFDiagCursor if corner in ('tl', 'br') else Qt.SizeBDiagCursor)
        # Handle NÃO é selecionável nem movável
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        # Aceita TODOS os botões do mouse
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton | Qt.MiddleButton)
        self._is_resizing = False

    def mousePressEvent(self, event):
        # Inicia redimensionamento
        self._is_resizing = True
        event.accept()

    def mouseMoveEvent(self, event):
        # Redimensiona durante o movimento do mouse
        if self._is_resizing:
            self.parent_node.resize_from_corner(self.corner, event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event):
        # Finaliza o redimensionamento
        self._is_resizing = False
        event.accept()
class StyledNode(QGraphicsRectItem):
    def __init__(self, x, y, w=200, h=100, node_type="Normal", brush=None):
        super().__init__(0, 0, w, h)

        self.setPos(x, y)
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape, True)

        self.node_type = node_type
        self.custom_color = None  # Stores custom background color hex if set
        self.has_shadow = True
        self.width = w
        self.height = h

        if brush is not None:
            self.setBrush(brush)
        else:
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0, QColor("#ffff00"))
            grad.setColorAt(1, QColor("#e8e813"))
            self.setBrush(QBrush(grad))
        self.setPen(QPen(Qt.NoPen))

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

        self.text = SelectionAwareTextItem(self)
        self.text.setTextWidth(w - 20)
        self.text.setPos(10, 10)
        if node_type in ["Preto", "Azul", "Refutar"]:
            self.text.setDefaultTextColor(Qt.white)
        else:
            self.text.setDefaultTextColor(Qt.black)
        self.text.setFont(QFont("Segoe UI", 11))
        self.text.setTextInteractionFlags(Qt.TextEditorInteraction)

        self.text.document().contentsChanged.connect(self._adjust_rect_to_text)
        self._center_text_vertical()

        # Media proxy/widget (inicialmente nenhum)
        self._media_proxy = None
        self._media_widget = None
        self._embedded_image = None

        self.handles = {}
        for corner in ('tl', 'tr', 'bl', 'br'):
            self.handles[corner] = Handle(self, corner)
        self._update_handle_positions()
        self._set_handles_visible(False)

    def _center_text_vertical(self):
        r = self.rect()
        tw = self.text.boundingRect().width()
        th = self.text.boundingRect().height()
        self.text.setTextWidth(max(20, r.width() - 20))
        th = self.text.boundingRect().height()
        y = max(10, (r.height() - th) / 2)
        self.text.setPos(10, y)

    def _adjust_rect_to_text(self):
        doc = self.text.document()
        if not doc.isEmpty():
            self.prepareGeometryChange()
            ideal = doc.size()
            r = self.rect()
            new_w = max(MIN_W, ideal.width() + 30)
            new_h = max(MIN_H, ideal.height() + 30)
            if new_w != r.width() or new_h != r.height():
                super().setRect(0, 0, new_w, new_h)
                self.text.setTextWidth(max(20, new_w - 20))
                self._center_text_vertical()
                self._update_handle_positions()
                self._update_media_proxy_geometry()
                self.width = new_w
                self.height = new_h

    def _update_handle_positions(self):
        r = self.rect()
        w, h = r.width(), r.height()
        self.handles['tl'].setPos(0, 0)
        self.handles['tr'].setPos(w, 0)
        self.handles['bl'].setPos(0, h)
        self.handles['br'].setPos(w, h)
        # Atualiza posição/size do proxy de mídia se existir
        self._update_media_proxy_geometry()

    def _set_handles_visible(self, visible):
        for h in self.handles.values():
            h.setVisible(visible)

    def resize_from_corner(self, corner, scene_pos):
        self.prepareGeometryChange()
        local = self.mapFromScene(scene_pos)
        r = self.rect()
        px, py = self.pos().x(), self.pos().y()
        w, h = r.width(), r.height()

        if corner == 'tl':
            new_w = (px + w) - (px + local.x())
            new_h = (py + h) - (py + local.y())
            new_w = max(MIN_W, min(new_w, w))
            new_h = max(MIN_H, min(new_h, h))
            self.setPos(px + w - new_w, py + h - new_h)
            super().setRect(0, 0, new_w, new_h)
        elif corner == 'tr':
            new_w = max(MIN_W, local.x())
            new_h = (py + h) - (py + local.y())
            new_h = max(MIN_H, min(new_h, h))
            self.setPos(px, py + h - new_h)
            super().setRect(0, 0, new_w, new_h)
        elif corner == 'bl':
            new_w = (px + w) - (px + local.x())
            new_w = max(MIN_W, min(new_w, w))
            new_h = max(MIN_H, local.y())
            self.setPos(px + w - new_w, py)
            super().setRect(0, 0, new_w, new_h)
        else:  # br
            new_w = max(MIN_W, local.x())
            new_h = max(MIN_H, local.y())
            super().setRect(0, 0, new_w, new_h)

        self.text.setTextWidth(max(20, self.rect().width() - 20))
        self._center_text_vertical()
        self._update_handle_positions()
        self._update_media_proxy_geometry()
        self.width = self.rect().width()
        self.height = self.rect().height()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self._set_handles_visible(bool(value))
        if change == QGraphicsRectItem.ItemPositionChange:
            main = QApplication.activeWindow()
            if hasattr(main, "alinhar_ativo") and main.alinhar_ativo:
                pos = value
                return pos.__class__(round(pos.x() / 20) * 20, round(pos.y() / 20) * 20)
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        """Renderiza o nó com a imagem incorporada se houver"""
        # Renderizar o background e border do nó
        super().paint(painter, option, widget)

        # Se há uma imagem incorporada, renderizá-la
        if self._embedded_image:
            r = self.rect()
            # Posicionar a imagem abaixo do texto
            img_y = 40
            img_x = 5
            
            # Escalar a imagem para caber no nó
            max_w = r.width() - 10
            max_h = r.height() - img_y - 5
            
            scaled = self._embedded_image.scaled(
                int(max_w), int(max_h),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Desenhar a imagem
            painter.drawPixmap(int(img_x), int(img_y), scaled)

    # -------------------------------
    # MÍDIA (PLAYLIST E IMAGENS)
    # -------------------------------
    def attach_media_player(self, media_list):
        """Anexa mídia ao nó: playlist para vídeos/áudios ou imagem incorporada.
        
        Para vídeos/áudios: Mostra apenas a lista (playlist)
        Para imagens: Incorpora a imagem direto no nó
        """
        if not media_list:
            return

        # Separar imagens de vídeos/áudios
        images = [m for m in media_list if self._is_image(m)]
        videos_audios = [m for m in media_list if not self._is_image(m)]

        # Se há imagem, incorporá-la
        if images:
            self._add_image_to_node(images[0])  # Usar primeira imagem

        # Se há vídeos/áudios, mostrar playlist
        if videos_audios:
            self._add_playlist_to_node(videos_audios)

    def _is_image(self, path: str) -> bool:
        """Verifica se é uma imagem"""
        path = path.lower()
        return any(path.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))

    def _add_image_to_node(self, image_path: str):
        """Incorpora uma imagem ao nó (não em widget, renderizada direto)"""
        try:
            from PySide6.QtGui import QPixmap
            import urllib.request

            # Carregar imagem
            if image_path.startswith(('http://', 'https://')):
                # Adicionar User-Agent para evitar 403 Forbidden
                req = urllib.request.Request(
                    image_path,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                data = urllib.request.urlopen(req, timeout=6).read()
                pix = QPixmap()
                pix.loadFromData(data)
            else:
                pix = QPixmap(image_path)

            if not pix.isNull():
                # Armazenar a imagem para renderizar no paint
                self._embedded_image = pix
                # Ajustar tamanho do nó para a imagem
                self._adjust_size_for_image(pix)
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")

    def _adjust_size_for_image(self, pixmap):
        """Ajusta o tamanho do nó para acomodar a imagem"""
        # Calcular tamanho ideal
        max_w = 400
        max_h = 300
        w = min(pixmap.width(), max_w)
        h = min(pixmap.height(), max_h)

        self.prepareGeometryChange()
        super().setRect(0, 0, max(w, 200), h + 40)  # 40px extra para espaço
        self.width = w
        self.height = h + 40

    def _add_playlist_to_node(self, media_list):
        """Adiciona uma playlist (vídeos/áudios) ao nó"""
        try:
            from core.media_widget import MediaPlaylistWidget
        except Exception as e:
            print(f"Erro ao importar MediaPlaylistWidget: {e}")
            return

        if self._media_proxy is None:
            widget = MediaPlaylistWidget()
            proxy = QGraphicsProxyWidget(self)
            proxy.setWidget(widget)
            proxy.setZValue(50)
            self._media_proxy = proxy
            self._media_widget = widget
        else:
            widget = self._media_widget

        widget.set_playlist(media_list or [])

        # Aumentar altura do nó para acomodar a playlist
        self.prepareGeometryChange()
        r = self.rect()
        if r.height() < 200:
            super().setRect(0, 0, r.width(), 200)
            self.height = 200

        self._update_media_proxy_geometry()

    def remove_media_player(self):
        if self._media_proxy:
            try:
                self.scene().removeItem(self._media_proxy)
            except Exception:
                pass
            self._media_proxy = None
            self._media_widget = None
        self._embedded_image = None

    def _update_media_proxy_geometry(self):
        """Posiciona e redimensiona o proxy de mídia dentro do nó."""
        if not self._media_proxy:
            return

        r = self.rect()
        pw = max(100, int(r.width()) - 10)
        ph = 140
        x = 5
        text_area_height = max(60, r.height() - 160)
        y = text_area_height
        self._media_proxy.setPos(x, y)
        self._media_proxy.widget().setFixedWidth(pw)
        self._media_proxy.widget().setFixedHeight(ph)

    # -------------------------------
    # CORES E ESTILOS
    # -------------------------------
    def update_color(self):
        if self.node_type in NODE_COLORS:
            colors = NODE_COLORS[self.node_type]
            grad = QLinearGradient(0, 0, 0, self.rect().height())
            grad.setColorAt(0, QColor(colors["light"]))
            grad.setColorAt(1, QColor(colors["dark"]))
            self.setBrush(QBrush(grad))

    def set_node_type(self, node_type):
        self.node_type = node_type
        self.custom_color = None
        self.update_color()
        if node_type in ["Preto", "Azul", "Refutar"]:
            self.text.setDefaultTextColor(Qt.white)
        else:
            self.text.setDefaultTextColor(Qt.black)

    def toggle_shadow(self):
        if self.has_shadow:
            self.setGraphicsEffect(None)
            self.has_shadow = False
        else:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setOffset(2, 2)
            shadow.setColor(QColor(0, 0, 0, 100))
            self.setGraphicsEffect(shadow)
            self.has_shadow = True

    # -------------------------------
    # TEXTO
    # -------------------------------
    def get_text(self):
        return self.text.toPlainText()

    def set_text(self, txt):
        self.text.setPlainText(txt)

    def set_font(self, font):
        self.text.setFont(font)

    def set_background(self, color):
        self.custom_color = color.name()
        grad = QLinearGradient(0, 0, 0, self.rect().height())
        grad.setColorAt(0, color.lighter(115))
        grad.setColorAt(1, color.darker(110))
        self.setBrush(QBrush(grad))

    def clone_without_content(self):
        r = self.rect()
        clone = StyledNode(self.x() + 30, self.y() + 30, int(r.width()), int(r.height()),
                          self.node_type, brush=self.brush())
        clone.custom_color = self.custom_color
        if self.graphicsEffect():
            sh = QGraphicsDropShadowEffect()
            sh.setBlurRadius(10)
            sh.setOffset(2, 2)
            sh.setColor(QColor(0, 0, 0, 100))
            clone.setGraphicsEffect(sh)
            clone.has_shadow = True
        return clone
