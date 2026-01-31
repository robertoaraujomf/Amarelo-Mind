#!/usr/bin/env python3
"""
Teste da nova abordagem de mídia:
1. Vídeos/Áudios: Apenas playlist (sem controles)
2. Imagens: Incorporadas ao nó (renderizadas direto)
"""

import sys
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from items.shapes import StyledNode


def test_new_media_approach():
    """Testa a nova abordagem de mídia"""
    
    print("=" * 60)
    print("TESTE: Nova abordagem de mídia")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Criar cena
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setGeometry(100, 100, 1000, 600)
    view.setWindowTitle("Teste: Vídeos/Áudios (playlist) vs Imagens (incorporadas)")
    
    # Teste 1: Vídeos/Áudios (apenas playlist)
    print("\nTeste 1: Vídeo + Playlist")
    node1 = StyledNode(50, 50, 350, 120, "Normal")
    node1.text.setPlainText("Playlist de Vídeos YouTube")
    scene.addItem(node1)
    
    videos = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    ]
    node1.attach_media_player(videos)
    print("  ✓ Nó 1: Vídeos com playlist")
    
    # Teste 2: Áudio Local (apenas playlist)
    print("\nTeste 2: Áudio Local")
    node2 = StyledNode(450, 50, 350, 120, "Azul")
    node2.text.setPlainText("Áudio Local (Playlist)")
    scene.addItem(node2)
    
    # Simular áudio local (URL fictícia para teste)
    audios = [
        "file:///C:/Music/song1.mp3",
        "file:///C:/Music/song2.mp3",
    ]
    node2.attach_media_player(audios)
    print("  ✓ Nó 2: Áudio com playlist")
    
    # Teste 3: Imagem Incorporada
    print("\nTeste 3: Imagem Incorporada")
    node3 = StyledNode(50, 300, 300, 200, "Amarelo")
    node3.text.setPlainText("Imagem Incorporada")
    scene.addItem(node3)
    
    # Usar uma imagem de exemplo
    image_url = "https://www.python.org/static/community_logos/python-logo.png"
    node3.attach_media_player([image_url])
    print("  ✓ Nó 3: Imagem incorporada")
    
    # Teste 4: Vídeo + Imagem
    print("\nTeste 4: Vídeo + Imagem")
    node4 = StyledNode(450, 300, 350, 200, "Verde")
    node4.text.setPlainText("Vídeo com Imagem")
    scene.addItem(node4)
    
    mixed = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.python.org/static/community_logos/python-logo.png",
    ]
    node4.attach_media_player(mixed)
    print("  ✓ Nó 4: Vídeo + Imagem incorporada")
    
    print("\n" + "=" * 60)
    print("RESULTADO: Nova abordagem implementada!")
    print("=" * 60)
    print("\nCaracterísticas:")
    print("  1. Vídeos/Áudios: Apenas playlist (sem play/pause/slider)")
    print("  2. Imagens: Incorporadas ao nó (renderizadas direto)")
    print("  3. Duplo clique em item da playlist abre no navegador")
    print("\n" + "=" * 60)
    
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_new_media_approach()
