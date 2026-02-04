
import sys
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QGraphicsTextItem
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtCore import Qt

# Ensure we can import from current directory
sys.path.append(".")

from main import AmareloMainWindow
from items.shapes import StyledNode

app = QApplication.instance() or QApplication(sys.argv)

class TestUndoRedo(unittest.TestCase):
    def setUp(self):
        self.win = AmareloMainWindow()
        self.win.show()
        
        # Add a node
        self.node = StyledNode(0, 0)
        self.win.scene.addItem(self.node)
        self.node.setSelected(True)
        self.win.update_button_states()

    def tearDown(self):
        self.win.close()

    def test_set_node_style_undo_redo(self):
        print("\nTesting set_node_style Undo/Redo...")
        initial_type = self.node.node_type
        
        # Change style
        self.win.set_node_style("Preto")
        self.assertEqual(self.node.node_type, "Preto")
        
        # Undo
        self.win.undo_stack.undo()
        self.assertEqual(self.node.node_type, initial_type)
        
        # Redo
        self.win.undo_stack.redo()
        self.assertEqual(self.node.node_type, "Preto")
        print("PASS: set_node_style Undo/Redo")

    @patch('PySide6.QtWidgets.QColorDialog.getColor')
    def test_change_background_color_undo_redo(self, mock_get_color):
        print("\nTesting change_colors (Background) Undo/Redo...")
        mock_get_color.return_value = QColor("#ff0000") # Red
        
        # Ensure no text selection
        cursor = self.node.text.textCursor()
        cursor.clearSelection()
        self.node.text.setTextCursor(cursor)
        
        # Change color
        self.win.change_colors()
        self.assertEqual(self.node.custom_color, "#ff0000")
        
        # Undo
        self.win.undo_stack.undo()
        self.assertIsNone(self.node.custom_color)
        
        # Redo
        self.win.undo_stack.redo()
        self.assertEqual(self.node.custom_color, "#ff0000")
        print("PASS: change_colors (Background) Undo/Redo")

    @patch('PySide6.QtWidgets.QColorDialog.getColor')
    def test_change_text_color_undo_redo(self, mock_get_color):
        print("\nTesting change_colors (Text) Undo/Redo...")
        mock_get_color.return_value = QColor("#0000ff") # Blue
        
        self.node.text.setPlainText("Hello")
        
        # Select text
        cursor = self.node.text.textCursor()
        cursor.select(QTextCursor.Document)
        self.node.text.setTextCursor(cursor)
        
        # Change color
        self.win.change_colors()
        
        # Check color (checking HTML or char format)
        cursor = self.node.text.textCursor()
        # Just check if HTML contains color or format
        html = self.node.text.toHtml()
        self.assertIn("#0000ff", html)
        
        # Undo
        self.win.undo_stack.undo()
        html_undo = self.node.text.toHtml()
        self.assertNotIn("#0000ff", html_undo)
        
        # Redo
        self.win.undo_stack.redo()
        html_redo = self.node.text.toHtml()
        self.assertIn("#0000ff", html_redo)
        print("PASS: change_colors (Text) Undo/Redo")

    @patch('PySide6.QtWidgets.QFontDialog.getFont')
    def test_change_font_undo_redo(self, mock_get_font):
        print("\nTesting change_font Undo/Redo...")
        font = QFont("Arial", 20)
        mock_get_font.return_value = (True, font)  # ORDEM CORRETA: (ok, font)
        
        initial_font = self.node.text.font()
        
        # Change font
        self.win.change_font()
        
        # Check font (since no selection, it applies to whole item)
        # But wait, change_font logic:
        # if cursor.hasSelection() -> mergeCharFormat
        # else -> item.set_font(font)
        
        current_font = self.node.text.font()
        # Compare family and size
        self.assertEqual(current_font.family(), "Arial")
        self.assertEqual(current_font.pointSize(), 20)
        
        # Undo
        self.win.undo_stack.undo()
        undo_font = self.node.text.font()
        self.assertNotEqual(undo_font.pointSize(), 20)
        
        # Redo
        self.win.undo_stack.redo()
        redo_font = self.node.text.font()
        self.assertEqual(redo_font.pointSize(), 20)
        print("PASS: change_font Undo/Redo")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
