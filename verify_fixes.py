
import sys
import os
import json
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from items.shapes import StyledNode
from core.persistence import PersistenceManager

def test_persistence_custom_color():
    print("Testing Persistence of Custom Color...")
    app = QApplication.instance() or QApplication(sys.argv)
    scene = QGraphicsScene()
    
    # Create node with custom color
    node = StyledNode(0, 0, 100, 50, "Normal")
    custom_color = QColor("#123456")
    node.set_background(custom_color)
    scene.addItem(node)
    
    assert node.custom_color == "#123456"
    
    # Save
    pm = PersistenceManager()
    test_file = "test_persistence.amind"
    pm.save_to_file(test_file, scene)
    
    # Clear and Load
    scene.clear()
    pm.load_from_file(test_file, scene)
    
    loaded_node = None
    for item in scene.items():
        if isinstance(item, StyledNode):
            loaded_node = item
            break
            
    assert loaded_node is not None, "StyledNode not found in scene"
    
    # Check if custom color persisted
    print(f"Loaded custom_color: {loaded_node.custom_color}")
    assert loaded_node.custom_color == "#123456"
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
    print("Persistence Test Passed!")

def test_resize_logic():
    print("Testing Resize Logic...")
    app = QApplication.instance() or QApplication(sys.argv)
    
    node = StyledNode(100, 100, 200, 100)
    
    # Simulate Drag on BR Handle
    # Start at 300, 200 (exact corner)
    # Move to 350, 250
    
    br_handle = node.handles['br']
    
    # Mock Event
    class MockEvent:
        def __init__(self, pos):
            self._pos = pos
        def scenePos(self):
            return self._pos
        def accept(self): pass

    # Press at corner (no snap if exact)
    start_pos = QPointF(300, 200) 
    br_handle.mousePressEvent(MockEvent(start_pos))
    
    # Move
    target_pos = QPointF(350, 250)
    br_handle.mouseMoveEvent(MockEvent(target_pos))
    
    r = node.rect()
    print(f"New size: {r.width()}x{r.height()}")
    
    assert r.width() == 250
    assert r.height() == 150
    
    br_handle.mouseReleaseEvent(MockEvent(target_pos))
    print("Resize Test Passed!")

if __name__ == "__main__":
    try:
        test_persistence_custom_color()
        test_resize_logic()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
