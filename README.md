# Amarelo Mind - Manual do Usuário

## 🎯 Visão Geral

**Amarelo Mind** é uma aplicação para criar e gerenciar mapas mentais interativos com suporte a múltiplos estilos de cores, persistência de dados e filtros avançados.

## 📦 Instalação

### Pré-requisitos
- Python 3.10+
- PySide6
- PIL (Pillow)
- NumPy (opcional, para PySide6)

### Setup
```bash
# Clonar ou entrar no diretório
cd "c:\Projetos\Amarelo\Amarelo Mind"

# Instalar dependências (se não tiver)
pip install PySide6 Pillow

# Executar
python main.py
```

## 🚀 Começando Rápido

### 1. Criar seu Primeiro Nó
- Pressione `+` ou clique no botão "Adicionar"
- Digite o texto desejado
- Pressione Enter

### 2. Aplicar Cor/Estilo
Selecione o nó e pressione um número de 1-9:
- `1` = Preto
- `2` = Azul
- `3` = Desfocar (Verde)
- `4` = Realçar (Amarelo)
- `5` = Exportar (Laranja)
- `6` = Desstacar (Roxo)
- `7` = Refutar (Vermelho)
- `8` = Explorar (Ciano)
- `9` = Colorir (Rosa)

### 3. Conectar Nós
- Selecione múltiplos nós na ordem que quer conectá-los
- Pressione `C` ou clique em "Conectar"

### 4. Salvar Seu Trabalho
- Pressione `Ctrl+S` para salvar
- Escolha local e formato (`.amr` ou `.json`)

## 🎨 Estilos de Nó Detalhados

| Estilo | Atalho | Cor | Uso Sugerido |
|--------|--------|-----|--------------|
| **Preto** | 1 | #333333 → #000000 | Categorias principais |
| **Azul** | 2 | #87ceeb → #0078d4 | Informações importantes |
| **Desfocar** | 3 | #c8e6c9 → #66bb6a | Itens secundários |
| **Realçar** | 4 | #fff59d → #fbc02d | Pontos chave |
| **Exportar** | 5 | #ffccbc → #ff7043 | Itens para exportar |
| **Desstacar** | 6 | #b39ddb → #7e57c2 | Destaques especiais |
| **Refutar** | 7 | #ef9a9a → #e53935 | Argumentos a refutar |
| **Explorar** | 8 | #80deea → #00acc1 | Áreas a pesquisar |
| **Colorir** | 9 | #f8bbd0 → #e91e63 | Marcação personalizada |

## 🎯 Funcionalidades Principais

### Arquivo
| Ação | Atalho | Descrição |
|------|--------|-----------|
| Novo | Ctrl+N | Abre nova janela |
| Abrir | Ctrl+A | Carrega projeto salvo |
| Salvar | Ctrl+S | Salva projeto |
| Exportar PNG | - | Salva como imagem |

### Edição
| Ação | Atalho | Descrição |
|------|--------|-----------|
| Desfazer | Ctrl+Z | Reverter última ação |
| Refazer | Ctrl+Y | Refazer ação |
| Copiar | Ctrl+C | Copia texto do nó |
| Colar | Ctrl+V | Cola texto no nó |
| Deletar | Delete | Remove seleção |

### Objetos
| Ação | Atalho | Descrição |
|------|--------|-----------|
| Adicionar | + | Novo nó |
| Conectar | C | Une nós com linha |
| Agrupar | - | Agrupa nós selecionados |
| Alinhar | A | Toggle snap to grid |

### Estilo
| Ação | Atalho | Descrição |
|------|--------|-----------|
| Fonte | - | Abre dialog de fonte |
| Cores | - | Abre color picker |
| Sombra | - | Toggle efeito sombra |

### Estilos Rápidos
| Atalho | Estilo |
|--------|--------|
| 1-9 | Estilos de cor predefinidos |

## 🔍 Filtros e Seleção

### Selecionar por Tipo
```
Seleciona todos os nós de um estilo específico
```
Exemplo: Selecionar todos os nós "Refutar" para análise

### Selecionar por Texto
```
Encontra nós contendo uma palavra-chave
```
Exemplo: Buscar "importante"

### Estatísticas
```
View → Estatísticas (se disponível)
```
Mostra contagem por tipo, total de nós, etc.

## 💾 Salvando e Carregando

### Formato .amr (Recomendado)
- Formato nativo do Amarelo Mind
- Preserva toda a informação
- Estrutura JSON comprimida

### Formato .json
- JSON puro para compatibilidade
- Pode ser editado manualmente
- Estrutura legível

### Estrutura Salva
```json
{
  "version": "1.0",
  "nodes": [
    {
      "id": 12345,
      "x": 100.0,
      "y": 200.0,
      "w": 200,
      "h": 100,
      "text": "Conteúdo",
      "type": "Azul",
      "shadow": true
    }
  ],
  "connections": [
    {
      "source_id": 12345,
      "target_id": 67890
    }
  ]
}
```

## 🎮 Navegação no Canvas

### Mover Vista
- **Pan**: Click + Drag em área vazia
- **Zoom**: Scroll do mouse (aproximar/afastar)

### Seleção
- **Selecionar**: Click em nó
- **Multi-seleção**: Ctrl + Click
- **Seleção Retangular**: Click + Drag em área vazia
- **Desselecionar Tudo**: Escape ou Click em área vazia

### Movimento
- **Mover Nó**: Click + Drag em nó selecionado
- **Múltiplos**: Selecionar e arrastar

## 💡 Dicas e Truques

### 1. Workflow Eficiente
```
1. Criar estrutura básica (todos Normal)
2. Adicionar conexões
3. Aplicar estilos por categoria
4. Revisar e refinar
5. Salvar e exportar
```

### 2. Organização
- Use cores para categorizar ideias
- Agrupe itens relacionados
- Adicione sombra a itens críticos

### 3. Filtros Avançados
```python
# Selecionar múltiplos grupos
Select tipo "Azul" + "Realçar" para análise
```

### 4. Exportação
- PNG para apresentações
- JSON para análise de dados
- Impressão direta (Print Screen + Paint)

## 🐛 Troubleshooting

### Problema: A aplicação não inicia
**Solução**: Verificar instalação do PySide6
```bash
pip install --upgrade PySide6
```

### Problema: Ícones não aparecem
**Solução**: Verificar pasta `assets/icons/`
Certifique-se de que os arquivos `.png` existem

### Problema: Arquivo não salva
**Solução**: Verificar permissões de pasta
Tentar salvar em outro local

## 📚 Estrutura de Arquivos

```
Amarelo Mind/
├── main.py                 # Aplicação principal
├── exemplos_uso.py         # Exemplos de código
├── test_features.py        # Testes de features
├── REQUISITOS.md           # Documentação de requisitos
├── README.md               # Este arquivo
├── assets/
│   ├── styles.qss
│   └── icons/
├── items/
│   ├── shapes.py           # Classe StyledNode
│   ├── node_styles.py      # Definições de cores
│   └── ...
└── core/
    ├── persistence.py      # Salvar/Carregar
    ├── item_filter.py      # Filtros
    ├── connection.py       # Conexões
    └── ...
```

## 🤝 Contribuindo

Para contribuir com melhorias:

1. Faça suas alterações
2. Teste com `python test_features.py`
3. Execute `exemplos_uso.py` para demonstração
4. Documente novas funcionalidades em `REQUISITOS.md`

## 📄 Licença

Amarelo Mind © 2026 - Projeto Educacional

## 📞 Suporte

Para dúvidas ou relatórios de bugs, consulte:
- `REQUISITOS.md` - Documentação técnica
- `exemplos_uso.py` - Exemplos de código
- `test_features.py` - Teste de funcionalidades

---

**Versão**: 1.0  
**Última Atualização**: Janeiro 2026  
**Autor**: Desenvolvedor Amarelo Mind
