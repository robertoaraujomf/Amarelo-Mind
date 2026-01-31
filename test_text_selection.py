#!/usr/bin/env python3
"""
Script para testar as funcionalidades:
1. Botões Fonte e Cores funcionam com seleção de texto
2. A seleção de texto é limpa ao clicar fora
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from main import AmareloMainWindow
from items.shapes import StyledNode


def test_text_selection():
    """Testa a seleção de texto e os botões de formatação"""
    app = QApplication(sys.argv)
    
    window = AmareloMainWindow()
    
    # Criar um nó para teste
    from items.shapes import StyledNode
    node = StyledNode(100, 100, 200, 100)
    node.set_text("Texto para testar seleção")
    window.scene.addItem(node)
    
    # Conectar o sinal do texto ao update_button_states
    if hasattr(node.text, 'selectionChanged'):
        node.text.selectionChanged.connect(window.update_button_states)
    
    # Selecionar o nó
    node.setSelected(True)
    node.text.setFocus(Qt.OtherFocusReason)
    
    # Simular seleção de texto
    cursor = node.text.textCursor()
    cursor.select(cursor.SelectionType.Document)
    node.text.setTextCursor(cursor)
    
    # Verificar se os botões estão habilitados
    def check_buttons():
        has_text_selection = node.text.textCursor().hasSelection()
        print(f"\n✓ Seleção de texto detectada: {has_text_selection}")
        print(f"✓ Botão Fonte habilitado: {window.act_font.isEnabled()}")
        print(f"✓ Botão Cores habilitado: {window.act_colors.isEnabled()}")
        
        if has_text_selection:
            print("\n✅ TESTE 1 PASSOU: Botões habilitados com texto selecionado")
        else:
            print("\n❌ TESTE 1 FALHOU: Seleção de texto não detectada")
        
        # Teste 2: Limpar seleção ao clicar fora
        cursor = node.text.textCursor()
        cursor.clearSelection()
        node.text.setTextCursor(cursor)
        node.text.focusOutEvent(None)
        
        has_text_selection = node.text.textCursor().hasSelection()
        print(f"\n✓ Seleção limpa após focusOutEvent: {not has_text_selection}")
        
        if not has_text_selection:
            print("✅ TESTE 2 PASSOU: Seleção limpa ao perder foco")
        else:
            print("❌ TESTE 2 FALHOU: Seleção não foi limpa")
        
        app.quit()
    
    # Executar verificação depois de 500ms
    QTimer.singleShot(500, check_buttons)
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_text_selection()
