#!/usr/bin/env python3
import sys
import os

# Suppress warnings
os.environ.setdefault("QT_LOGGING_RULES", "qt.webengine.*=false;qt.qpa.gl=false")
os.environ.setdefault("QT_NO_PORTAL", "1")

# Setup path
sys.path.insert(0, '/home/roberto/Projetos/Amarelo-Mind')

from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QAction

# Import IconManager
from core.icon_manager import IconManager
IconManager.set_icons_base('/home/roberto/Projetos/Amarelo-Mind')

app = QApplication(sys.argv)
app.setApplicationName("TestIcons")

window = QMainWindow()
window.setWindowTitle("Teste de Ícones")

tb = QToolBar("Toolbar")
tb.setIconSize(QSize(40, 40))
tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
window.addToolBar(tb)

icons_to_test = [
    ("Novo.png", "Novo"),
    ("Abrir.png", "Abrir"),
    ("Salvar.png", "Salvar"),
    ("Exportar.png", "Exportar"),
    ("Desfazer.png", "Desfazer"),
    ("Refazer.png", "Refazer"),
    ("Copiar.png", "Copiar"),
    ("Colar.png", "Colar"),
    ("Adicionar.png", "Adicionar"),
    ("Titulo.png", "Título"),
    ("Midia.png", "Mídia"),
    ("Conectar.png", "Conectar"),
    ("Excluir.png", "Excluir"),
    ("Fonte.png", "Fonte"),
    ("Cores.png", "Cores"),
    ("Localizar.png", "Localizar"),
]

for icon_name, tooltip in icons_to_test:
    icon = IconManager.load_icon(icon_name, icon_name[0])
    action = QAction(icon, tooltip, window)
    tb.addAction(action)
    print(f"✓ {icon_name}: loaded={not icon.isNull()}")

window.resize(800, 100)
window.show()

print("\nToolbar aberta! Verifique os ícones...")
sys.exit(app.exec())
