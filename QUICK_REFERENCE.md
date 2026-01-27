# 🎯 GUIA RÁPIDO - AMARELO MIND

## Iniciar
```bash
python main.py
```

---

## 🎨 Cores Rápidas (Pressione 1-9)

| Tecla | Cor | Uso |
|-------|-----|-----|
| 1 | ⬛ Preto | Categorias |
| 2 | 🔵 Azul | Importante |
| 3 | 🟢 Desfocar | Secundário |
| 4 | 🟡 Realçar | Destaque |
| 5 | 🟠 Exportar | Para Export |
| 6 | 🟣 Desstacar | Destaque 2 |
| 7 | 🔴 Refutar | Refutar |
| 8 | 🔷 Explorar | Pesquisar |
| 9 | 🩷 Colorir | Custom |

---

## ⌨️ Atalhos Principais

**Arquivo**
- `Ctrl+N` → Novo
- `Ctrl+A` → Abrir
- `Ctrl+S` → Salvar

**Editar**
- `Ctrl+Z` → Desfazer
- `Ctrl+Y` → Refazer
- `Ctrl+C` → Copiar
- `Ctrl+V` → Colar

**Objetos**
- `+` → Adicionar nó
- `C` → Conectar nós
- `Delete` → Excluir
- `A` → Toggle alinhar

---

## 🔍 Operações Rápidas

### Seleção
1. **Click** = Selecionar um
2. **Ctrl+Click** = Adicionar à seleção
3. **Drag vazio** = Seleção retangular
4. **Escape** = Desselecionar tudo

### Edição
1. **Duplo-clique** = Editar texto
2. **Drag** = Mover
3. **Scroll** = Zoom
4. **Drag vazio** = Pan (panning)

### Estilo
1. Selecionar nó(s)
2. Pressionar 1-9 para cor
3. Usar botões para fonte/cores custom/sombra

---

## 💾 Salvar/Carregar

**Salvar**
```
Ctrl+S → Escolher local → .amr ou .json
```

**Carregar**
```
Ctrl+A → Selecionar arquivo → Confirmar
```

---

## 🔎 Filtros

No código (exemplos_uso.py):
```python
# Por tipo
window.item_filter.select_by_type("Azul")

# Por texto
window.item_filter.select_by_text("importante")

# Estatísticas
stats = window.item_filter.get_statistics()
```

---

## 📊 Casos de Uso

### Brainstorm
1. Criar nós (Normal)
2. Conectar ideias (C)
3. Categorizar (cores 1-9)
4. Salvar (Ctrl+S)

### Análise
1. Usar cores para categorias
2. Agrupar nós relacionados
3. Filtrar por tipo
4. Exportar PNG

### Apresentação
1. Organizar layout
2. Aplicar cores coerentes
3. Adicionar sombra para destaque
4. Exportar PNG

---

## 🚀 Dicas Pro

1. **Magnetismo** (A): Ativa snap to grid para alinhamento
2. **Sombra**: Usa efeito drop shadow em nós críticos
3. **Agrupar**: Para itens relacionados (Agrupar button)
4. **Fonte**: Muda tamanho/tipo (Fonte button)
5. **Cores Custom**: Para marcações especiais (Cores button)

---

## 📁 Arquivos Úteis

- `README.md` → Manual completo
- `REQUISITOS.md` → Documentação técnica
- `exemplos_uso.py` → 5 exemplos práticos
- `CHECKLIST_VALIDACAO.md` → Status completo

---

## ❓ FAQ Rápido

**P: Como editar texto?**
A: Selecione o nó e comece a digitar, ou duplo-clique

**P: Como salvar automaticamente?**
A: Pressione Ctrl+S frequentemente

**P: Posso usar cores custom?**
A: Sim! Clique no botão "Cores" para color picker

**P: Como criar um mapa complexo?**
A: Veja exemplos_uso.py → example_5_complex_mindmap()

**P: Posso exportar para PDF?**
A: Não yet, mas pode exportar como PNG e converter

---

## ⚡ Workflow Otimizado

1. **Setup** (2min)
   - Abrir Amarelo Mind
   - Ctrl+N para novo projeto

2. **Criar** (10min)
   - Pressionar + para nós
   - C para conectar
   - 1-9 para cores

3. **Refinar** (5min)
   - Alinhar com A
   - Fonte/cores conforme necessário
   - Sombra em pontos-chave

4. **Salvar** (1min)
   - Ctrl+S
   - Escolher .amr ou .json

5. **Exportar** (1min)
   - Exportar PNG (botão ou File menu)

---

**Versão**: 1.0  
**Última atualização**: Jan 2026  
**Status**: ✓ Completo
