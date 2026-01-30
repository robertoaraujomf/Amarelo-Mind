
import sys
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtCore import QPointF, Qt
from items.shapes import StyledNode

def test_resize():
    app = QApplication.instance() or QApplication(sys.argv)
    scene = QGraphicsScene(0, 0, 1000, 1000)
    view = QGraphicsView(scene)
    
    # Create a node
    node = StyledNode(100, 100, 200, 100, "Normal")
    scene.addItem(node)
    
    # Select the node to show handles
    node.setSelected(True)
    
    # Verify handles are created
    assert len(node.handles) == 4
    
    # Get the bottom-right handle
    br_handle = node.handles['br']
    assert br_handle.isVisible()
    
    # Initial geometry
    initial_rect = node.rect()
    initial_pos = node.pos()
    print(f"Initial Rect: {initial_rect}, Pos: {initial_pos}")
    
    # Simulate mouse press on the handle
    # We need to map scene coordinates to handle coordinates if we were sending events manually,
    # but here we can just call the event handlers directly or simulate via scene.
    
    # Let's try to simulate dragging the BR handle by +50, +50
    start_scene_pos = br_handle.scenePos() + QPointF(5, 5) # Center of handle roughly
    
    # Create a MouseEvent? 
    # It's easier to just call the methods if we want to unit test the logic,
    # but to test the ItemIsMovable interaction we'd ideally use the event system.
    
    # However, since we removed ItemIsMovable, we want to ensure custom logic works.
    
    # Simulate Drag
    target_scene_pos = start_scene_pos + QPointF(50, 50)
    
    # 1. Press
    # We can't easily synthesize a QGraphicsSceneMouseEvent without a view, 
    # but we can call mousePressEvent directly.
    
    # Mock event class
    class MockEvent:
        def __init__(self, pos):
            self._pos = pos
        def scenePos(self):
            return self._pos
        def accept(self):
            pass
            
    # Press
    br_handle.mousePressEvent(MockEvent(start_scene_pos))
    
    # Move
    br_handle.mouseMoveEvent(MockEvent(target_scene_pos))
    
    # Check new geometry
    new_rect = node.rect()
    print(f"New Rect: {new_rect}")
    
    expected_width = initial_rect.width() + 50
    expected_height = initial_rect.height() + 50
    
    # Allow some float tolerance
    assert abs(new_rect.width() - expected_width) < 1.0, f"Width mismatch: {new_rect.width()} != {expected_width}"
    assert abs(new_rect.height() - expected_height) < 1.0, f"Height mismatch: {new_rect.height()} != {expected_height}"
    
    # Check position (BR handle shouldn't move the top-left of the node)
    new_pos = node.pos()
    assert new_pos == initial_pos, f"Position changed: {new_pos} != {initial_pos}"
    
    # Release
    br_handle.mouseReleaseEvent(MockEvent(target_scene_pos))
    
    print("Test Passed!")

if __name__ == "__main__":
    test_resize()
