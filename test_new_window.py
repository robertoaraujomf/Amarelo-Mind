
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from main import AmareloMainWindow

class TestNewWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_new_window_is_independent(self):
        main_window = AmareloMainWindow()
        initial_windows = len(QApplication.topLevelWidgets())
        
        with patch('main.AmareloMainWindow') as mock_main_window:
            main_window.new_window()
            self.assertEqual(mock_main_window.call_count, 1)

if __name__ == '__main__':
    unittest.main()
