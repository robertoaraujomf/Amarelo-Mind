#!/usr/bin/env python
"""Teste básico do fluxo de mídia"""

import sys
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path(__file__).parent))

# Imports
from items.shapes import StyledNode
from core.media_widget import MediaPlayerWidget

def test_media_player_visibility():
    """Teste se o player fica visível quando mídia é adicionada"""
    print("Testing MediaPlayerWidget visibility...")
    
    # Criar um nó
    node = StyledNode(100, 100, 200, 100, "Normal")
    
    # Altura original
    original_height = node.rect().height()
    print(f"  Altura original do nó: {original_height}")
    
    # Adicionar mídia (simular attach_media_player)
    test_playlist = [
        "https://www.youtube.com/watch?v=test123",
        "https://www.youtube.com/watch?v=test456"
    ]
    
    node.attach_media_player(test_playlist)
    
    # Altura após adicionar mídia
    new_height = node.rect().height()
    print(f"  Altura do nó após adicionar mídia: {new_height}")
    
    # Validar que a altura aumentou
    if new_height >= 320:
        print("  ✓ Altura do nó aumentou corretamente (>= 320)")
    else:
        print(f"  ✗ Altura do nó não é suficiente: {new_height} < 320")
    
    # Validar que o proxy foi criado
    if node._media_proxy is not None:
        print("  ✓ Media proxy foi criado")
    else:
        print("  ✗ Media proxy não foi criado")
    
    # Validar que o widget foi criado
    if node._media_widget is not None:
        print("  ✓ Media widget foi criado")
    else:
        print("  ✗ Media widget não foi criado")
    
    print("\nTeste concluído!")

if __name__ == "__main__":
    test_media_player_visibility()
