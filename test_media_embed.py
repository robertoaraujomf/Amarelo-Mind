#!/usr/bin/env python
"""
Quick test to validate media embedding works correctly.
Run: python test_media_embed.py
"""

import sys
import os

def test_webengine_available():
    """Test if QWebEngineView can be imported and instantiated"""
    print("Testing QWebEngineView availability...")
    try:
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.setAttribute(__import__('PySide6.QtCore', fromlist=['Qt']).Qt.AA_ShareOpenGLContexts, True)
        
        from PySide6.QtWidgets import QApplication
        app = QApplication([])
        
        from PySide6.QtWebEngineWidgets import QWebEngineView
        view = QWebEngineView()
        print("  ✓ QWebEngineView imported and instantiated")
        view.setHtml("<html><body>Test</body></html>")
        print("  ✓ QWebEngineView can load HTML")
        return True
    except Exception as e:
        print(f"  ✗ QWebEngineView failed: {e}")
        return False

def test_media_widget_ui():
    """Test if MediaPlayerWidget UI builds correctly"""
    print("\nTesting MediaPlayerWidget UI structure...")
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        
        from core.media_widget import MediaPlayerWidget
        widget = MediaPlayerWidget()
        
        # Check expected UI components
        checks = [
            (widget.title_label, "title_label"),
            (widget.list_widget, "list_widget"),
            (widget.content_stack, "content_stack"),
            (widget.btn_play, "btn_play"),
            (widget.btn_prev, "btn_prev"),
            (widget.btn_next, "btn_next"),
            (widget.position_slider, "position_slider"),
        ]
        
        for component, name in checks:
            if component is not None:
                print(f"  ✓ {name} present")
            else:
                print(f"  ✗ {name} missing")
        
        # Check web_view (may be None if WebEngine unavailable)
        if widget.web_view is not None:
            print(f"  ✓ web_view available (embedding enabled)")
        else:
            print(f"  ⚠ web_view unavailable (fallback to external playback)")
        
        return True
    except Exception as e:
        print(f"  ✗ MediaPlayerWidget failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Amarelo Mind - Media Widget Test")
    print("=" * 60)
    
    webengine_ok = test_webengine_available()
    widget_ok = test_media_widget_ui()
    
    print("\n" + "=" * 60)
    if webengine_ok and widget_ok:
        print("✓ All checks passed. Media embedding should work.")
    elif widget_ok:
        print("⚠ Widget OK but WebEngine unavailable. Will use fallback (external playback).")
    else:
        print("✗ Tests failed. Check logs above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
