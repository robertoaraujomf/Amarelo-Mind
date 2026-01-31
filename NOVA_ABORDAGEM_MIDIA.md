# 🎬 NOVA ABORDAGEM DE MÍDIA - Documentação

## Mudança de Estratégia

### Antes (Abordagem Anterior)
```
Vídeos/Áudios    → Player com todos os controles (play, pause, slider, etc)
Imagens          → Exibidas em um widget separado (QLabel com pixmap)
```

### Agora (Nova Abordagem) ✨
```
Vídeos/Áudios    → APENAS PLAYLIST (lista de títulos, sem controles)
Imagens          → INCORPORADAS AO NÓ (renderizadas direto, não widget)
```

---

## 1. Vídeos/Áudios - Apenas Playlist

### Como Funciona
- Mostra uma lista de títulos (vídeos ou áudios)
- Duplo clique em um item abre no navegador (YouTube) ou no player padrão (local)
- **Sem controles de play/pause/slider**
- Widget leve: `MediaPlaylistWidget`

### Exemplo de Uso
```python
node = StyledNode(50, 50, 300, 150)
videos = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",
]
node.attach_media_player(videos)
```

### Resultado Visual
```
┌─────────────────────┐
│ Meus Vídeos      [M]│
├─────────────────────┤
│ Playlist:           │
│ • Vídeo 1           │
│ • Vídeo 2           │
│ [Duplo clique]      │
└─────────────────────┘
```

---

## 2. Imagens - Incorporadas ao Nó

### Como Funciona
- Imagem é carregada e **renderizada direto no nó**
- Não é um widget separado
- Usa o método `paint()` para renderizar
- Redimensiona automaticamente para caber no nó
- Suporta URLs remotas e arquivos locais

### Exemplo de Uso
```python
node = StyledNode(50, 300, 300, 250)
node.text.setPlainText("Imagem Exemplo")
image = ["https://example.com/image.png"]
node.attach_media_player(image)
```

### Resultado Visual
```
┌──────────────────────┐
│ Imagem Exemplo    [M]│
├──────────────────────┤
│                      │
│    [Imagem aqui]     │
│    renderizada       │
│    direto no nó      │
└──────────────────────┘
```

---

## 3. Misto - Vídeo + Imagem

### Como Funciona
- Se passar vídeo + imagem, ambos são processados
- Imagem é incorporada ao nó
- Vídeo aparece como playlist

### Exemplo de Uso
```python
node = StyledNode(50, 50, 350, 300)
media = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://example.com/image.png"
]
node.attach_media_player(media)
```

### Resultado Visual
```
┌──────────────────────────┐
│ Vídeo + Imagem        [M]│
├──────────────────────────┤
│ Playlist:                │
│ • Vídeo 1                │
│                          │
│ [Imagem renderizada]     │
└──────────────────────────┘
```

---

## Mudanças no Código

### 1. `core/media_widget.py`
- **Removido:** `MediaPlayerWidget` (com controles)
- **Adicionado:** `MediaPlaylistWidget` (apenas lista)
- Sem `QMediaPlayer`, sem `QSlider`, sem botões

### 2. `items/shapes.py`
- **Adicionado:** `paint()` para renderizar imagens
- **Mudado:** `attach_media_player()` agora diferencia vídeos/áudios de imagens
- **Adicionado:** `_is_image()`, `_add_image_to_node()`, `_add_playlist_to_node()`
- **Adicionado:** `_embedded_image` para armazenar imagens

### 3. Métodos Principais
```python
# Detecta o tipo de mídia
_is_image(path)  → True se PNG/JPG/GIF/WebP/BMP

# Processa imagem
_add_image_to_node(path)  → Carrega e incorpora

# Processa vídeo/áudio
_add_playlist_to_node(list)  → Cria widget de playlist

# Renderiza tudo
paint(painter, option, widget)  → Desenha nó + imagem
```

---

## Benefícios

### ✅ Simplicidade
- Sem controles desnecessários
- Interface limpa

### ✅ Performance
- Imagens não são widgets (mais leve)
- Playlist é um widget simples

### ✅ Usabilidade
- Duplo clique para abrir (intuitivo)
- Imagens sempre visíveis
- Playlist ocupar menos espaço

### ✅ Compatibilidade
- Continua funcionando com `QGraphicsProxyWidget`
- Sem dependências pesadas

---

## Como Testar

### Teste Automático
```bash
python test_new_media_approach.py
```

### Teste Manual
```bash
python main.py
# 1. Selecione um nó
# 2. Pressione "M" para adicionar mídia
# 3. Teste com:
#    - Vídeos: https://www.youtube.com/watch?v=dQw4w9WgXcQ
#    - Imagens: https://www.python.org/static/community_logos/python-logo.png
```

---

## Casos de Uso

### 1. Galeria de Imagens
```python
node.attach_media_player(["image1.jpg", "image2.jpg", "image3.jpg"])
# Mostra primeira imagem incorporada
```

### 2. Playlist de Vídeos YouTube
```python
node.attach_media_player([
    "https://www.youtube.com/watch?v=...",
    "https://www.youtube.com/watch?v=...",
])
# Duplo clique abre no navegador
```

### 3. Coleção de Áudio
```python
node.attach_media_player([
    "file:///music/song1.mp3",
    "file:///music/song2.mp3",
])
# Duplo clique toca no player padrão
```

### 4. Artigo com Imagem
```python
node.text.setPlainText("Artigo sobre Python")
node.attach_media_player(["python-logo.png"])
# Imagem aparece abaixo do texto
```

---

## Limitações Atuais

| Limitação | Solução Futura |
|-----------|---|
| Controles de play não visíveis | Adicionar atalhos de teclado |
| Imagem não é clicável | Adicionar ação ao clicar na imagem |
| Sem preview de vídeo | Adicionar thumbnail de vídeo |
| Sem volume control | Não necessário (abre em navegador) |

---

## Próximas Melhorias (Backlog)

- [ ] Suporte a múltiplas imagens (carousel)
- [ ] Ação ao clicar na imagem (abrir em navegador)
- [ ] Thumbnail de vídeo YouTube
- [ ] Atalhos de teclado (espaço = play)
- [ ] Persistência da mídia (salvar com nó)

---

## Conclusão

A nova abordagem é **mais simples, mais leve e mais intuitiva**:
- ✅ Vídeos/Áudios como playlist (sem clutter)
- ✅ Imagens incorporadas (parte do nó)
- ✅ Interface limpa
- ✅ Performance melhorada

---

**Status:** ✅ IMPLEMENTADO E TESTADO
