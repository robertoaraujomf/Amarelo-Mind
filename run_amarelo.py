#!/usr/bin/env python3
"""
Amarelo Mind - Launcher with suppressed WebEngine noise.
"""

import sys
import os

# Suppress WebEngine warnings before any Qt imports
os.environ.setdefault("QT_LOGGING_RULES",
    "qt.webengine.*=false;qt.qpa.gl=false;js.*=false;*doh*=false")

# Suppress DBus portal warnings
os.environ.setdefault("QT_NO_PORTAL", "1")

# Detect if running from installed location or development
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")):
    base_dir = os.path.dirname(os.path.abspath(__file__))
else:
    base_dir = "/usr/share/amarelo-mind"

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

icons_dir = os.path.join(base_dir, "assets", "icons")
os.environ["AMARELO_ICON_PATH"] = icons_dir

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

import main

app = QApplication.instance() or QApplication(sys.argv)

app.setApplicationName("amarelo-mind")
app.setApplicationDisplayName("Amarelo Mind")
app.setDesktopFileName("amarelo-mind")

icon_path = os.path.join(icons_dir, "App_icon.ico")
if os.path.exists(icon_path):
    app.setWindowIcon(QIcon(icon_path))
else:
    icon_path = os.path.join(icons_dir, "App_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

file_to_load = None
if len(sys.argv) > 1:
    file_path = sys.argv[1]
    if file_path.endswith('.amind') and os.path.exists(file_path):
        file_to_load = file_path

window = main.AmareloMainWindow()

if file_to_load:
    window.load_file(file_to_load)

try:
    window.setWindowRole("main")
except Exception:
    pass

window.showMaximized()

sys.exit(app.exec())
