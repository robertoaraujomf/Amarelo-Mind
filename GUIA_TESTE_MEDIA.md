# 🎬 GUIA RÁPIDO - TESTANDO O MEDIA PLAYER

## Pré-requisitos
Nenhum! A solução já está implementada.

---

## Método 1: Teste Automatizado (Recomendado)
Roda todos os testes automaticamente:
```bash
python validate_media_fix.py
```

Resultado esperado:
```
[SUCCESS] All tests passed!
[OK] Media player is fully integrated and working!
```

---

## Método 2: Teste Manual Interativo
Lança a app completa para teste manual:
```bash
python test_manual_media.py
```

**O que fazer:**
1. Selecione um nó no canvas (clique em um)
2. Pressione "M" ou vá ao menu → Adicionar Mídia
3. Na janela de diálogo, cole uma URL:
   - **Vídeo único:** `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
   - **Playlist:** `https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf`
4. Clique em OK
5. **Observar:** Media player aparece DENTRO do nó (não em janela separada)

---

## Método 3: Teste Granular
Testa cada componente isoladamente:

### Teste 1: Widget básico
```bash
python test_new_media_widget.py
```

### Teste 2: Integração completa
```bash
python test_integration_media.py
```

---

## O que Esperar

### ✅ Ao adicionar um vídeo:
```
[Nó com vídeo]
┌─────────────────────────────┐
│ Rick Astley - Never...      │
│ [⏮ ▶️ ⏭]    [=========]     │
├─────────┬─────────────────┤
│ Playlist│  [Thumbnail]    │
│         │                 │
│         │  Clique ▶️ para │
│         │  abrir no nav.  │
└─────────┴─────────────────┘
```

### ✅ Ao adicionar uma playlist:
```
[Nó com playlist]
┌──────────────────────────────┐
│ Playlist de vídeos           │
│ [⏮ ▶️ ⏭]    [=========]      │
├────────────┬────────────────┤
│ • Video 1  │  [Thumbnail    │
│ • Video 2  │   do primeiro  │
│ • Video 3  │   vídeo]       │
│            │                │
│ [clique    │  Duplo clique  │
│  duplo]    │  para abrir    │
└────────────┴────────────────┘
```

### ✅ Ao adicionar uma imagem:
```
[Nó com imagem]
┌──────────────────────────────┐
│ Minha Imagem                 │
│         [Imagem exibida]     │
│         [Em tamanho real]    │
└──────────────────────────────┘
```

---

## Checklist de Verificação

Ao testar, confirme que:

- [ ] **Nenhuma janela separada aparece** quando adiciona mídia
- [ ] Media player fica **dentro do nó** (não à parte)
- [ ] **Lista de vídeos** aparece à esquerda (para playlists)
- [ ] **Thumbnail/preview** aparece à direita
- [ ] Botões **⏮ ▶️ ⏭** funcionam
- [ ] **Duplo clique em um vídeo** abre no navegador
- [ ] **Slider de progresso** funciona para áudio local
- [ ] **Imagens locais** aparecem embutidas
- [ ] **Sem erros** no console

---

## Troubleshooting

### Problema: "Erro ao anexar player"
**Solução:** Veja a mensagem de erro no console. A app agora registra erros em vez de silenciar.

### Problema: "Vídeo não carrega"
**Solução:** 
- Para YouTube: precisa de conexão internet
- Para arquivo local: use caminho absoluto
- Tipos suportados: MP3, MP4, WebM, WAV, etc

### Problema: "Playlist vazia"
**Solução:**
- Verifique se a URL da playlist é válida
- Tente: `https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf`
- A extração é por web scraping (pode demorar alguns segundos)

### Problema: "Encoding error no terminal"
**Solução:** Normal no Windows. Use `validate_media_fix.py` que já trata isso.

---

## URLs de Teste

Copie e cole estas URLs para testar:

### Vídeos
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=jNQXAC9IVRw
https://www.youtube.com/watch?v=9bZkp7q19f0
```

### Playlists
```
https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
https://www.youtube.com/playlist?list=PLPE1oJW-PKbQfYj2BdTjHsqN4xfQMfF-b
```

### Arquivos Locais
```
/caminho/para/seu/audio.mp3
/caminho/para/seu/video.mp4
/caminho/para/sua/imagem.jpg
```

---

## Dicas Avançadas

### 1. Adicionar múltiplas mídias
Você pode adicionar mídia a vários nós. Cada nó tem seu próprio player.

### 2. Atualizar a playlist
Selecione o nó de novo e pressione "M" para adicionar ou atualizar.

### 3. Remover mídia
Selecione o nó e procure por uma opção de remover player (se existir no seu menu).

---

## Feedback Esperado

Se tudo funcionar corretamente, você verá:
```
Testing new lightweight media widget...

[OK] MediaPlayerWidget created successfully
[OK] Playlist loaded successfully
[OK] Widget successfully embedded in QGraphicsProxyWidget

[SUCCESS] All tests passed! New media widget is ready.
```

---

## Próximas Etapas

1. ✅ Validar que tudo funciona (`validate_media_fix.py`)
2. ✅ Testar com URLs reais (`test_manual_media.py`)
3. ✅ Usar normalmente no app (`python main.py`)
4. 📝 Reportar qualquer problema que encontrar

---

**Divirta-se usando o media player! 🎬**
