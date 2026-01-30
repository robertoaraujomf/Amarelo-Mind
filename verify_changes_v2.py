
import sys
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from items.shapes import StyledNode, Handle

def test_handle_properties():
    app = QApplication.instance() or QApplication(sys.argv)
    scene = QGraphicsScene()
    node = StyledNode(0, 0)
    scene.addItem(node)
    
    # Check handle size
    # StyledNode creates handles in update_handles -> set_selected(True)
    node.setSelected(True)
    
    # Find handles
    handles = [i for i in node.childItems() if isinstance(i, Handle)]
    if not handles:
        print("FAIL: No handles found")
        return
        
    h = handles[0]
    rect = h.rect()
    print(f"Handle Rect: {rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}")
    
    expected_width = 14
    if rect.width() == expected_width:
        print("PASS: Handle size is correct.")
    else:
        print(f"FAIL: Handle width {rect.width()} != {expected_width}")

    # Test Mouse Press Event
    class MockEvent:
        def __init__(self, button):
            self._button = button
            self._accepted = False
        def button(self): return self._button
        def accept(self): self._accepted = True
        def isAccepted(self): return self._accepted
        def ignore(self): pass

    # Test Left Button
    evt_left = MockEvent(Qt.LeftButton)
    h.mousePressEvent(evt_left)
    if evt_left.isAccepted():
        print("PASS: Handle accepted Left Button")
    else:
        print("FAIL: Handle ignored Left Button")

    # Test Right Button
    evt_right = MockEvent(Qt.RightButton)
    h.mousePressEvent(evt_right)
    if evt_right.isAccepted():
        print("PASS: Handle accepted Right Button")
    else:
        print("FAIL: Handle ignored Right Button")

if __name__ == "__main__":
    try:
        test_handle_properties()
        print("All tests finished.")
    except Exception as e:
        print(f"Test crashed: {e}")
