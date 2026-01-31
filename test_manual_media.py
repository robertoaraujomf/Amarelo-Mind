"""
Manual test script: Launch app and test adding media to a node
Run this and:
1. Click on a node to select it
2. Press "M" to open media dialog
3. Paste a YouTube URL
4. Check if media player appears inside the node (NOT in separate window)
"""
import sys
from PySide6.QtWidgets import QApplication
from main import AmareloMind

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    print("\n" + "="*60)
    print("AMARELO MIND - MEDIA PLAYER TEST")
    print("="*60)
    print("\nInstructions:")
    print("  1. Select a node in the canvas")
    print("  2. Press 'M' to open media dialog")
    print("  3. Add a YouTube URL or playlist")
    print("  4. Verify that:")
    print("     ✓ Media player appears INSIDE the node")
    print("     ✓ NO separate window appears")
    print("     ✓ Playlist is shown on the left")
    print("     ✓ Video thumbnail appears on the right")
    print("\nTest URLs:")
    print("  • Single video: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print("  • Playlist: https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")
    print("="*60 + "\n")
    
    window = AmareloMind()
    window.show()
    sys.exit(app.exec())
