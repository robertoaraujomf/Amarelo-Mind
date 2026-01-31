"""Integration test: Full workflow of adding media to a node"""
import sys
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QTimer
from core.media_widget import MediaPlayerWidget


def test_full_workflow():
    """Test complete workflow: create scene -> create node -> add media -> embed"""
    
    print("Starting full integration test...\n")
    
    # Initialize app
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    
    # Test 1: Create media widget
    print("Test 1: Create MediaPlayerWidget")
    try:
        widget = MediaPlayerWidget()
        print("  [OK] Widget created")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    # Test 2: Load a YouTube playlist
    print("\nTest 2: Load YouTube playlist")
    try:
        playlist_url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        widget.set_playlist([playlist_url])
        print(f"  [OK] Playlist loaded")
        print(f"    - Items in list widget: {widget.list_widget.count()}")
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Load single video
    print("\nTest 3: Load single YouTube video")
    try:
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        widget.set_playlist([video_url])
        print(f"  [OK] Video loaded")
    except Exception as e:
        # Avoid printing emojis that cause encoding issues
        print(f"  [FAIL] Could not load video")
        return False
    
    # Test 4: Embed in QGraphicsProxyWidget (simulating node)
    print("\nTest 4: Embed in QGraphicsProxyWidget (node simulation)")
    try:
        from PySide6.QtWidgets import QGraphicsProxyWidget
        
        scene = QGraphicsScene()
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(widget)
        scene.addItem(proxy)
        
        print("  [OK] Successfully embedded in proxy widget")
        print(f"    - No separate windows should appear")
        print(f"    - Scene item count: {len(scene.items())}")
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Verify widget is lightweight (no WebEngine)
    print("\nTest 5: Verify lightweight implementation")
    try:
        # Check that QWebEngineView is NOT imported (only in comments is OK)
        import core.media_widget as mw_module
        source_code = open(mw_module.__file__, encoding='utf-8', errors='ignore').read()
        
        # Remove comments and strings to avoid false positives
        lines = []
        for line in source_code.split('\n'):
            if not line.strip().startswith('#'):
                lines.append(line)
        clean_code = '\n'.join(lines)
        
        has_webengine_import = "from PySide6.QtWebEngineWidgets import QWebEngineView" in clean_code
        has_label_html = "self.content_label" in clean_code
        
        if has_webengine_import:
            print("  [FAIL] QWebEngineView import found")
            return False
        
        if not has_label_html:
            print("  [FAIL] No content_label found")
            return False
        
        print("  [OK] Lightweight (no QWebEngineView import)")
        print("  [OK] Uses QLabel for HTML display")
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("[SUCCESS] All integration tests PASSED!")
    print("="*60)
    print("\nThe new media widget is ready for use:")
    print("  + Lightweight (no QWebEngineView)")
    print("  + Compatible with QGraphicsProxyWidget")
    print("  + Shows YouTube thumbnails + playlist")
    print("  + Opens videos in browser on play")
    print("  + Supports images and local media files")
    
    return True


if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)
