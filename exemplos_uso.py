"""
Exemplo de uso da API de Amarelo Mind programaticamente
Demonstra como usar os recursos implementados
"""

from PySide6.QtWidgets import QApplication
from main import AmareloMainWindow
from items.shapes import StyledNode
from core.connection import SmartConnection
import sys


def example_1_create_nodes_with_styles():
    """
    Exemplo 1: Criar nós com diferentes estilos
    """
    app = QApplication.instance() or QApplication([])
    window = AmareloMainWindow()
    
    # Criar nós base
    node1 = StyledNode(100, 100, 200, 100, "Normal")
    node1.set_text("Ideia Central")
    window.scene.addItem(node1)
    
    # Nós com estilos específicos
    styles = ["Preto", "Azul", "Desfocar", "Realçar", "Exportar", 
              "Desstacar", "Refutar", "Explorar", "Colorir"]
    
    for i, style in enumerate(styles):
        x = 400 + (i % 3) * 250
        y = 100 + (i // 3) * 150
        node = StyledNode(x, y, 200, 100, style)
        node.set_text(f"Nó {style}")
        window.scene.addItem(node)
        # Conectar ao nó central
        connection = SmartConnection(node1, node)
        window.scene.addItem(connection)
    
    window.show()
    return app, window


def example_2_filter_and_select():
    """
    Exemplo 2: Usar filtros para selecionar itens
    """
    app = QApplication.instance() or QApplication([])
    window = AmareloMainWindow()
    
    # Criar vários nós
    nodes = []
    for i in range(9):
        style = ["Normal", "Azul", "Refutar", "Normal", "Azul", 
                 "Explorar", "Normal", "Desfocar", "Realçar"][i]
        node = StyledNode(100 + i * 150, 100, 120, 80, style)
        node.set_text(f"Item {i+1}\n({style})")
        window.scene.addItem(node)
        nodes.append(node)
    
    # Usar filtros
    print("Total de nós:", len(nodes))
    print("\nEstatísticas:")
    stats = window.item_filter.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Selecionar apenas nós "Azul"
    print("\nSelecionando nós 'Azul'...")
    window.item_filter.select_by_type("Azul")
    
    window.show()
    return app, window


def example_3_save_and_load():
    """
    Exemplo 3: Salvar e carregar projeto
    """
    import os
    
    app = QApplication.instance() or QApplication([])
    window = AmareloMainWindow()
    
    # Criar alguns nós
    node1 = StyledNode(100, 100, 200, 100, "Azul")
    node1.set_text("Conceito Principal")
    window.scene.addItem(node1)
    node1.toggle_shadow()
    
    node2 = StyledNode(400, 100, 200, 100, "Realçar")
    node2.set_text("Ponto Importante")
    window.scene.addItem(node2)
    
    connection = SmartConnection(node1, node2)
    window.scene.addItem(connection)
    
    # Salvar projeto
    project_path = os.path.join(os.path.dirname(__file__), "exemplo_projeto.amr")
    success = window.persistence.save_to_file(project_path, window.scene)
    
    if success:
        print(f"✓ Projeto salvo em: {project_path}")
        
        # Limpar e carregar
        window.scene.clear()
        success = window.persistence.load_from_file(project_path, window.scene)
        
        if success:
            print(f"✓ Projeto carregado com sucesso!")
            print(f"  Nós na cena: {len([i for i in window.scene.items() if isinstance(i, StyledNode)])}")
    
    window.show()
    return app, window


def example_4_batch_style_application():
    """
    Exemplo 4: Aplicar estilos em lote
    """
    app = QApplication.instance() or QApplication([])
    window = AmareloMainWindow()
    
    # Criar matriz de nós
    for row in range(3):
        for col in range(3):
            node = StyledNode(100 + col * 200, 100 + row * 150, 180, 120, "Normal")
            node.set_text(f"Célula\n({row},{col})")
            window.scene.addItem(node)
    
    # Selecionar todos na primeira linha
    items = [i for i in window.scene.items() if isinstance(i, StyledNode)]
    for item in items[:3]:
        item.setSelected(True)
    
    # Aplicar estilo
    window.set_node_style("Azul")
    
    # Selecionar segunda linha
    window.scene.clearSelection()
    for item in items[3:6]:
        item.setSelected(True)
    
    window.set_node_style("Refutar")
    
    window.show()
    return app, window


def example_5_complex_mindmap():
    """
    Exemplo 5: Mapa mental complexo com múltiplas técnicas
    """
    app = QApplication.instance() or QApplication([])
    window = AmareloMainWindow()
    
    # Raiz central
    root = StyledNode(500, 300, 150, 80, "Azul")
    root.set_text("Projeto")
    window.scene.addItem(root)
    
    # Categorias principais
    categories = [
        ("Planejamento", "Realçar", 100, 100),
        ("Execução", "Explorar", 100, 400),
        ("Revisão", "Refutar", 900, 100),
        ("Melhoria", "Desfocar", 900, 400),
    ]
    
    for cat_name, style, x, y in categories:
        cat = StyledNode(x, y, 180, 100, style)
        cat.set_text(cat_name)
        window.scene.addItem(cat)
        
        # Conectar à raiz
        conn = SmartConnection(root, cat)
        window.scene.addItem(conn)
        
        # Adicionar subitens
        for i in range(2):
            sub = StyledNode(x, y + 150 + i * 120, 160, 80, "Normal")
            sub.set_text(f"Sub {i+1}")
            window.scene.addItem(sub)
            
            # Conectar à categoria
            sub_conn = SmartConnection(cat, sub)
            window.scene.addItem(sub_conn)
    
    window.show()
    return app, window


if __name__ == "__main__":
    # Escolha qual exemplo executar
    print("""
    Exemplos de Uso - Amarelo Mind
    ==============================
    
    1. Criar nós com diferentes estilos
    2. Filtrar e selecionar itens
    3. Salvar e carregar projeto
    4. Aplicar estilos em lote
    5. Mapa mental complexo
    
    Iniciando exemplo 5 (mapa mental complexo)...
    """)
    
    # Descomente o exemplo que quer executar
    app, window = example_5_complex_mindmap()
    
    sys.exit(app.exec())
