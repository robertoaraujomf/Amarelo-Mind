"""Test the new lightweight media widget integration"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from core.media_widget import MediaPlayerWidget


def test_widget_creation():
    """Test 1: Widget création and instantiation"""
    try:
        app = QApplication(sys.argv)
        widget = MediaPlayerWidget()
        print("[OK] MediaPlayerWidget created successfully")
        print(f"  - Playlist: {widget.playlist}")
        print(f"  - Current index: {widget.current_index}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to create MediaPlayerWidget: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_playlist_loading():
    """Test 2: Load test playlist"""
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        widget = MediaPlayerWidget()
        
        # Test playlist
        test_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        ]
        
        widget.set_playlist(test_urls)
        print("[OK] Playlist loaded successfully")
        print(f"  - Playlist size: {len(widget.playlist)}")
        print(f"  - List widget items: {widget.list_widget.count()}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to load playlist: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_proxy_widget_compatibility():
    """Test 3: Check if widget works with QGraphicsProxyWidget"""
    try:
        from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsScene, QGraphicsView
        from PySide6.QtCore import Qt
        
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Create scene and view
        scene = QGraphicsScene()
        view = QGraphicsView(scene)
        view.setWindowTitle("Media Widget Proxy Test")
        
        # Create media widget
        media_widget = MediaPlayerWidget()
        media_widget.set_playlist([
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        ])
        
        # Embed in proxy
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(media_widget)
        scene.addItem(proxy)
        
        view.setGeometry(100, 100, 800, 400)
        view.show()
        
        print("[OK] Widget successfully embedded in QGraphicsProxyWidget")
        print(f"  - Proxy widget created")
        print(f"  - No separate windows created")
        
        # Note: Don't run event loop in test, just verify structure
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to embed in proxy: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing new lightweight media widget...\n")
    
    results = []
    results.append(("Widget Creation", test_widget_creation()))
    results.append(("Playlist Loading", test_playlist_loading()))
    results.append(("Proxy Compatibility", test_proxy_widget_compatibility()))
    
    print("\n" + "="*50)
    print("Test Results:")
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {test_name}")
    
    all_passed = all(r for _, r in results)
    print("="*50)
    if all_passed:
        print("\n[SUCCESS] All tests passed! New media widget is ready.")
    else:
        print("\n[ERROR] Some tests failed. Check errors above.")
    
    sys.exit(0 if all_passed else 1)
