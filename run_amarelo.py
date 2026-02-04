#!/usr/bin/env python
"""
Amarelo Mind - Launcher with suppressed WebEngine noise.
Silences Chromium/Qt WebEngine console spam while keeping the app fully functional.
"""

import subprocess
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

def run_amarelo():
    """Run main.py with stderr redirected to devnull to suppress Chromium spam."""
    env = os.environ.copy()
    env.setdefault("QT_LOGGING_RULES", 
        "qt.webengine.*=false;qt.qpa.gl=false;js.*=false;*doh*=false")
    
    # Launch main.py with Chromium console output redirected
    # This silences "doh set to", "js: Error", "Failed to stop audio engine", etc.
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            env=env,
            stderr=subprocess.DEVNULL,  # Suppress Chromium stderr
            cwd=os.path.dirname(os.path.abspath(__file__)) or "."
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Failed to launch Amarelo Mind: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Configurar ícone da aplicação
    app = QApplication.instance() or QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "App_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    run_amarelo()
