#!/usr/bin/env python3
"""
Amarelo Mind - Launcher with suppressed WebEngine noise.
"""

import sys
import os

# Detect if running from installed location or development
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")):
    # Development mode
    base_dir = os.path.dirname(os.path.abspath(__file__))
else:
    # Installed mode - assume /usr/share/amarelo-mind
    base_dir = "/usr/share/amarelo-mind"

# Add base_dir to Python path
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Set environment variables for icon path
os.environ["AMARELO_ICON_PATH"] = os.path.join(base_dir, "assets", "icons")

# Suppress WebEngine warnings before any Qt imports
os.environ.setdefault("QT_LOGGING_RULES", 
    "qt.webengine.*=false;qt.qpa.gl=false;js.*=false;*doh*=false")

# Now import Qt and launch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

# Import main module
import main

# Create application instance
app = QApplication.instance() or QApplication(sys.argv)

# Set app identity for proper panel integration (fixes duplicate icon issue)
app.setApplicationName("AmareloMind")
app.setApplicationDisplayName("Amarelo Mind")
app.setDesktopFileName("AmareloMind")

# Set window icon
icon_path = os.path.join(base_dir, "assets", "icons", "App_icon.ico")
if os.path.exists(icon_path):
    app.setWindowIcon(QIcon(icon_path))
else:
    # Fallback to PNG
    icon_path = os.path.join(base_dir, "assets", "icons", "App_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

# Check if a file was passed as argument BEFORE creating window
file_to_load = None
if len(sys.argv) > 1:
    file_path = sys.argv[1]
    if file_path.endswith('.amind') and os.path.exists(file_path):
        file_to_load = file_path

# Create and show main window
window = main.AmareloMainWindow()

# Load file if provided
if file_to_load:
    window.load_file(file_to_load)

# Set window role for proper taskbar/dock grouping on Linux
try:
    window.setWindowRole("main")
except Exception:
    pass

window.show()

sys.exit(app.exec())
