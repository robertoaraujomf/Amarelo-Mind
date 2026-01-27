# Requisitos Implementados - Amarelo Mind

## Visão Geral
A aplicação Amarelo Mind foi adaptada para atender a todos os 17 requisitos especificados, incluindo 9 estilos de cor para nós, operações de edição, persistência de dados e filtros.

---

## 1. BOTÕES DE CORES ESPECÍFICAS (Requisitos 1-9)

### 1.1 Preto (Req. 1)
- **Atalho**: `1`
- **Cores**: #333333 (claro) → #000000 (escuro)
- **Ação**: Aplica estilo preto ao nó selecionado
- **Texto**: Branco para contraste

### 1.2 Azul (Req. 2)
- **Atalho**: `2`
- **Cores**: #87ceeb (claro) → #0078d4 (escuro)
- **Ação**: Aplica estilo azul ao nó selecionado
- **Uso**: Realçar informações importantes

### 1.3 Desfocar (Req. 3)
- **Atalho**: `3`
- **Cores**: #c8e6c9 (claro) → #66bb6a (escuro)
- **Ação**: Aplica estilo verde de desfocar
- **Uso**: Marcar informações secundárias

### 1.4 Realçar (Req. 4)
- **Atalho**: `4`
- **Cores**: #fff59d (claro) → #fbc02d (escuro)
- **Ação**: Aplica estilo amarelo para realçar
- **Uso**: Destaque de elementos importantes

### 1.5 Exportar (Req. 5)
- **Atalho**: `5`
- **Cores**: #ffccbc (claro) → #ff7043 (escuro)
- **Ação**: Aplica estilo laranja
- **Uso**: Marcar itens para exportação

### 1.6 Desstacar (Req. 6)
- **Atalho**: `6`
- **Cores**: #b39ddb (claro) → #7e57c2 (escuro)
- **Ação**: Aplica estilo roxo
- **Uso**: Marcar destaques secundários

### 1.7 Refutar (Req. 7)
- **Atalho**: `7`
- **Cores**: #ef9a9a (claro) → #e53935 (escuro)
- **Ação**: Aplica estilo vermelho
- **Uso**: Marcar argumentos a refutar

### 1.8 Explorar (Req. 8)
- **Atalho**: `8`
- **Cores**: #80deea (claro) → #00acc1 (escuro)
- **Ação**: Aplica estilo ciano
- **Uso**: Marcar áreas a explorar

### 1.9 Colorir (Req. 9)
- **Atalho**: `9`
- **Cores**: #f8bbd0 (claro) → #e91e63 (escuro)
- **Ação**: Aplica estilo rosa
- **Uso**: Marcação personalizada

---

## 2. OPERAÇÕES DE ARQUIVO

### Novo Mapa Mental
- **Atalho**: `Ctrl+N`
- **Ação**: Abre uma nova janela de Amarelo Mind

### Abrir Projeto
- **Atalho**: `Ctrl+A`
- **Funcionalidade**: Carrega projeto salvo anteriormente
- **Formatos**: `.amr` (Amarelo Mind), `.json`

### Salvar Projeto
- **Atalho**: `Ctrl+S`
- **Funcionalidade**: Salva o projeto atual
- **Dados Salvos**:
  - Posição (x, y)
  - Tamanho (largura, altura)
  - Conteúdo de texto
  - Tipo/estilo do nó
  - Estado de sombra
  - Conexões entre nós

### Exportar como PNG
- **Funcionalidade**: Exporta o mapa mental como imagem PNG
- **Recurso**: Transparência preservada

---

## 3. OPERAÇÕES DE EDIÇÃO

### Desfazer/Refazer
- **Desfazer**: `Ctrl+Z` / Botão "Desfazer"
- **Refazer**: `Ctrl+Y` / Botão "Refazer"
- **Suporte**: Undo/Redo stack integrado

### Copiar
- **Atalho**: `Ctrl+C`
- **Funcionalidade**: Copia texto do nó selecionado

### Colar
- **Atalho**: `Ctrl+V`
- **Funcionalidade**: Cola texto no nó selecionado

### Adicionar Objeto
- **Atalho**: `+`
- **Funcionalidade**: 
  - Se houver nó selecionado: cria novo nó abaixo com conexão
  - Se não: cria nó no centro da tela

### Excluir Objeto
- **Atalho**: `Delete`
- **Funcionalidade**: Remove item(ns) selecionado(s)

### Conectar Nós
- **Atalho**: `C`
- **Funcionalidade**: Cria conexões entre nós selecionados sequencialmente

### Agrupar
- **Funcionalidade**: Agrupa múltiplos nós selecionados
- **Características**:
  - Retângulo arredondado tracejado
  - Movimento conjunto
  - Desagrupamento disponível

---

## 4. EDIÇÃO DE ESTILO

### Fonte
- **Funcionalidade**: Dialog para alterar fonte do texto
- **Aplicado A**: Nós selecionados

### Cores (Personalizado)
- **Funcionalidade**: Color dialog para cores personalizadas
- **Aplicado A**: Nós selecionados

### Sombra
- **Funcionalidade**: Toggle de sombra gráfica
- **Efeito**: Drop shadow com desfoque

---

## 5. FILTROS E SELEÇÃO

### Filtrar por Tipo
- **Uso**: Seleciona todos os nós de um tipo específico
- **Exemplo**: Selecionar todos os nós "Refutar"

### Filtrar por Texto
- **Uso**: Seleciona todos os nós contendo um texto
- **Case-insensitive**: Sim

### Filtrar por Posição
- **Uso**: Seleciona nós em uma região específica
- **Parâmetros**: x_min, y_min, x_max, y_max

### Filtrar com Sombra
- **Uso**: Seleciona todos os nós que possuem sombra

### Estatísticas
- **Informações Retornadas**:
  - Total de itens
  - Contagem por tipo
  - Itens com/sem sombra

---

## 6. INTERATIVIDADE

### Canvas Infinito
- **Funcionalidade**: Área ilimitada para desenho
- **Navegação**: Pan com mouse (área vazia)
- **Zoom**: Scroll do mouse

### Magnetismo (Alinhar)
- **Atalho**: `A` / Botão "Alinhar"
- **Funcionalidade**: Snap to grid 20px
- **Toggle**: Pode ser ativado/desativado

### Seleção
- **Seleção Múltipla**: Ctrl+Click
- **Seleção Retangular**: Click+Drag em área vazia

---

## 7. ESTRUTURA DE DADOS

### Nó (StyledNode)
- `x, y`: Posição
- `w, h`: Dimensões
- `text`: Conteúdo textual
- `node_type`: Tipo/estilo (Normal, Preto, Azul, etc)
- `has_shadow`: Booleano indicando sombra

### Conexão (SmartConnection)
- `source`: Nó de origem
- `target`: Nó de destino
- `path`: Caminho curvo/reto adaptativo

### Grupo (GroupNode)
- `child_items`: Nós agrupados
- `is_unit`: Tratado como unidade

---

## 8. TECLADO - MAPA COMPLETO

| Atalho | Ação |
|--------|------|
| `Ctrl+N` | Novo mapa |
| `Ctrl+A` | Abrir projeto |
| `Ctrl+S` | Salvar projeto |
| `Ctrl+Z` | Desfazer |
| `Ctrl+Y` | Refazer |
| `Ctrl+C` | Copiar |
| `Ctrl+V` | Colar |
| `+` | Adicionar objeto |
| `C` | Conectar nós |
| `Delete` | Excluir selecionado |
| `A` | Toggle alinhar |
| `1` | Estilo Preto |
| `2` | Estilo Azul |
| `3` | Estilo Desfocar |
| `4` | Estilo Realçar |
| `5` | Estilo Exportar |
| `6` | Estilo Desstacar |
| `7` | Estilo Refutar |
| `8` | Estilo Explorar |
| `9` | Estilo Colorir |

---

## 9. PERSISTÊNCIA

### Formato de Arquivo
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
      "text": "Conteúdo do nó",
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

---

## 10. COMO USAR

### Iniciar Aplicação
```bash
python main.py
```

### Workflow Básico
1. Clique em "+" para adicionar nó
2. Digite o conteúdo
3. Selecione estilo com teclado (1-9) ou botão
4. Use "C" para conectar nós
5. Salve com `Ctrl+S`

### Filtrar Itens
```python
# No código
app.item_filter.select_by_type("Azul")
app.item_filter.select_by_text("importante")
stats = app.item_filter.get_statistics()
```

---

## 11. ARQUITETURA DE MÓDULOS

```
main.py                    # Janela principal e lógica
├── items/
│   ├── shapes.py         # Classe StyledNode
│   ├── node_styles.py    # Estilos e cores
│   ├── connection_label.py
│   ├── group_item.py     # Agrupamento
│   ├── group_box.py
│   └── base_node.py
├── core/
│   ├── icon_manager.py   # Gerenciador de ícones
│   ├── persistence.py    # Salvar/carregar
│   ├── item_filter.py    # Filtros
│   ├── connection.py     # Conexões entre nós
│   ├── text_editor.py
│   ├── style_manager.py
│   └── commands.py       # Undo/Redo
└── assets/
    ├── styles.qss        # Folha de estilos
    └── icons/            # Ícones PNG
```

---

## 12. ROADMAP FUTURO

- [ ] Temas de cores personalizáveis
- [ ] Histórico visual de alterações
- [ ] Exportação para PDF
- [ ] Colaboração em tempo real
- [ ] Templates de mapas mentais
- [ ] Plugin system
- [ ] Dark mode

---

**Versão**: 1.0  
**Última Atualização**: Janeiro 2026
