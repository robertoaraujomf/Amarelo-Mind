"""
Script de teste para demonstrar as funcionalidades da aplicação Amarelo Mind
"""

def test_node_styles():
    """Testa os estilos de nós disponíveis"""
    from items.node_styles import NODE_COLORS, NODE_STATE, NODE_ICONS
    
    print("=" * 50)
    print("ESTILOS DE NÓS DISPONÍVEIS")
    print("=" * 50)
    
    for style_name, colors in NODE_COLORS.items():
        print(f"\n{style_name}:")
        print(f"  Cor Clara: {colors['light']}")
        print(f"  Cor Escura: {colors['dark']}")
        if style_name != "Normal":
            print(f"  Atalho: {NODE_ICONS.get(style_name, 'N/A')}")


def test_filters():
    """Demonstra o uso de filtros"""
    print("\n" + "=" * 50)
    print("FILTROS DISPONÍVEIS")
    print("=" * 50)
    
    filters = [
        "- Filtro por tipo de nó",
        "- Filtro por texto contido",
        "- Filtro por posição/região",
        "- Filtro por presença de sombra",
        "- Estatísticas gerais"
    ]
    
    for f in filters:
        print(f)


def test_persistence():
    """Demonstra persistência de dados"""
    print("\n" + "=" * 50)
    print("PERSISTÊNCIA DE DADOS")
    print("=" * 50)
    
    print("\nFormatos suportados:")
    print("- .amr (Amarelo Mind Project)")
    print("- .json (JSON genérico)")
    
    print("\nDados salvos:")
    print("- Posição e tamanho dos nós")
    print("- Conteúdo de texto")
    print("- Tipo/estilo de cada nó")
    print("- Estado de sombra")
    print("- Conexões entre nós")


if __name__ == "__main__":
    test_node_styles()
    test_filters()
    test_persistence()
    
    print("\n" + "=" * 50)
    print("ATALHOS DE TECLADO")
    print("=" * 50)
    
    shortcuts = {
        "Ctrl+N": "Novo mapa mental",
        "Ctrl+A": "Abrir projeto",
        "Ctrl+S": "Salvar projeto",
        "Ctrl+C": "Copiar",
        "Ctrl+V": "Colar",
        "Delete": "Excluir selecionado",
        "+": "Adicionar objeto",
        "C": "Conectar nós",
        "1-9": "Aplicar estilo de cor (Preto, Azul, Desfocar, etc)",
        "A": "Toggle Alinhar"
    }
    
    for key, action in shortcuts.items():
        print(f"{key:15} -> {action}")
