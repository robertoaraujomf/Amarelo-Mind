#!/usr/bin/env python3
import sys
import os

# Set base directory
base_dir = "/usr/share/amarelo-mind"

# Suppress WebEngine warnings
os.environ.setdefault("QT_LOGGING_RULES", 
    "qt.webengine.*=false;qt.qpa.gl=false;js.*=false;*doh*=false")

# Add to path
sys.path.insert(0, base_dir)

# Set icon path
os.environ["AMarelo_ICON_PATH"] = os.path.join(base_dir, "assets", "icons", "App_icon.ico")

# Import and run
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import main

app = QApplication(sys.argv)
app.setApplicationName("AmareloMind")
app.setApplicationDisplayName("Amarelo Mind")

icon_path = os.path.join(base_dir, "assets", "icons", "App_icon.ico")
if os.path.exists(icon_path):
    app.setWindowIcon(QIcon(icon_path))

window = main.AmareloMainWindow()
window.show()
sys.exit(app.exec())
