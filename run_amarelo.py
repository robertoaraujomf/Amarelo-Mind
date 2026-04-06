#!/usr/bin/env python
"""
Amarelo Mind - Launcher with suppressed WebEngine noise.
"""

import sys
import os

# Add current directory to path
if hasattr(os, 'getcwd'):
    base_dir = os.getcwd()
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not base_dir:
        base_dir = "."

# Suppress WebEngine warnings before any Qt imports
os.environ.setdefault("QT_LOGGING_RULES", 
    "qt.webengine.*=false;qt.qpa.gl=false;js.*=false;*doh*=false")

# Now import Qt and launch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

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

# Check if a file was passed as argument BEFORE creating window
file_to_load = None
if len(sys.argv) > 1:
    file_path = sys.argv[1]
    print(f"DEBUG: Received file argument: {file_path}")
    if file_path.endswith('.amind') and os.path.exists(file_path):
        file_to_load = file_path
        print(f"DEBUG: Will load file: {file_to_load}")

# Create and show main window
window = main.AmareloMainWindow()

# Load file if provided
if file_to_load:
    print(f"DEBUG: Calling load_file with: {file_to_load}")
    window.load_file(file_to_load)

window.show()

sys.exit(app.exec())
