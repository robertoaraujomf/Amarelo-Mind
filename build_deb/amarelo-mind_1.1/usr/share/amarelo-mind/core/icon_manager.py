import os
import sys
from PySide6.QtWidgets import QInputDialog
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import QSize, Qt

class IconManager:
    """Gerencia ícones dos botões e inserção de emojis nos nós"""
    
    _icons_dir = None
    
    @staticmethod
    def set_icons_base(base_dir):
        """Define o diretório base do projeto (ex.: pasta do main.py). Ícones em base_dir/assets/icons."""
        resolved = os.path.abspath(base_dir)
        IconManager._icons_dir = os.path.normpath(os.path.join(resolved, "assets", "icons"))
    
    @staticmethod
    def _get_icons_dir():
        """Obtém o diretório assets/icons de forma robusta, tentando vários candidatos."""
        if IconManager._icons_dir is not None:
            return IconManager._icons_dir
        
        candidates = []
        
        # 1. Raiz do projeto a partir de core/icon_manager.py
        try:
            _here = os.path.abspath(__file__)
            base = os.path.dirname(os.path.dirname(_here))
            candidates.append(os.path.join(base, "assets", "icons"))
        except Exception:
            pass
        
        # 2. Diretório do script principal (main.py)
        try:
            if getattr(sys, "argv", None) and len(sys.argv) > 0:
                main_path = os.path.abspath(sys.argv[0])
                base = os.path.dirname(main_path)
                candidates.append(os.path.join(base, "assets", "icons"))
        except Exception:
            pass
        
        # 3. Diretório de trabalho atual
        try:
            cwd = os.getcwd()
            candidates.append(os.path.join(cwd, "assets", "icons"))
        except Exception:
            pass
        
        for path in candidates:
            if path and os.path.isdir(path):
                IconManager._icons_dir = os.path.normpath(path)
                return IconManager._icons_dir
        
        # Fallback: usa raiz a partir de __file__ mesmo que não exista (evita None)
        try:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fallback = os.path.normpath(os.path.join(base, "assets", "icons"))
        except Exception:
            fallback = os.path.normpath(os.path.join(os.getcwd(), "assets", "icons"))
        
        IconManager._icons_dir = fallback
        return IconManager._icons_dir
    
    @staticmethod
    def load_icon(filename, fallback_text=""):
        """Carrega um ícone do diretório assets/icons ou cria um fallback"""
        icons_dir = IconManager._get_icons_dir()
        icon_path = os.path.join(icons_dir, filename)
        
        # Tenta também com diferentes variações de case (Windows)
        if not os.path.exists(icon_path):
            # Lista arquivos no diretório para encontrar correspondência case-insensitive
            try:
                if os.path.exists(icons_dir):
                    for f in os.listdir(icons_dir):
                        if f.lower() == filename.lower():
                            icon_path = os.path.join(icons_dir, f)
                            break
            except:
                pass
        
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            # Fallback: cria um ícone simples com texto
            pixmap = QPixmap(40, 40)
            pixmap.fill(Qt.transparent)
            p = QPainter(pixmap)
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Arial", 20, QFont.Bold))
            p.drawText(pixmap.rect(), Qt.AlignCenter, fallback_text[:1] if fallback_text else "?")
            p.end()
            return QIcon(pixmap)
    
    @staticmethod
    def open_emoji_picker(parent, item):
        """Gerencia a inserção de emojis e ícones nos nós (Requisito 12)"""
        emojis = ["📌", "💡", "🚀", "✅", "❌", "⚠️", "🔥", "⭐", "📅", "👤"]
        emoji, ok = QInputDialog.getItem(parent, "Inserir Ícone", "Escolha um símbolo:", emojis, 0, False)
        
        if ok and emoji:
            current_text = item.text_item.toPlainText()
            item.text_item.setPlainText(f"{emoji} {current_text}")