# Amarelo Mind - Guia de Execução e Resolução de Problemas

## Iniciar a Aplicação

### Opção 1: Limpo (Recomendado - Sem logs de Chromium)
```powershell
cd "c:\Projetos\Amarelo\Amarelo Mind"
python run_amarelo.py
```
Isso suprime automaticamente mensagens internas do Chromium/Qt WebEngine como:
- "doh set to" (DNS diagnostics)
- "js: Error with Permissions-Policy" (avisos de página web)
- "Failed to stop audio engine" (cleanup interno)

### Opção 2: Direto
```powershell
cd "c:\Projetos\Amarelo\Amarelo Mind"
python main.py
```
Pode mostrar logs do WebEngine, mas a app funciona normalmente.

---

## Media Player (Playlist do YouTube)

1. **Selecione um objeto** no mapa mental (nó)
2. **Pressione "M"** ou clique no ícone **Mídia** na toolbar
3. **Escolha "URL Online"** e cole a URL de uma **playlist do YouTube**:
   ```
   https://www.youtube.com/playlist?list=XXXXX
   ```
4. **Clique OK**

### Resultado Esperado
- O nó **expande automaticamente** para 320px de altura
- **Player embutido** aparece no lado direito (vídeo em embed HTML5)
- **Lista de todos os vídeos** da playlist aparece no lado esquerdo
- **Controles de mídia** (⏮ ▶️ ⏭ e slider de progresso) funcionam
- **Clique duplo** em um título = carrega esse vídeo no player

---

## Variáveis de Ambiente (Troubleshooting)

Se você precisar debugar ou contornar problemas:

### Ver logs do WebEngine (para diagnóstico)
```powershell
$env:AMARELO_LOG_WEBENGINE = '1'
python main.py
```

### Forçar backend OpenGL específico
```powershell
$env:AMARELO_OPENGL = 'software'   # or 'desktop'
python main.py
```

### Desabilitar aceleração GPU do WebEngine
```powershell
$env:AMARELO_DISABLE_GPU = '1'
python main.py
```

### Desabilitar WebEngine embedding (fallback externo)
```powershell
$env:AMARELO_WEBENGINE_ENABLED = '0'
python main.py
```
Neste caso, ao clicar em play, um link será aberto no navegador padrão.

---

## Problemas Conhecidos e Resoluções

### Mensagens sobre "doh set to" ou "Permissions-Policy" na tela
- **Causa**: Chromium/Qt WebEngine emite esses avisos internamente
- **Solução**: Use `python run_amarelo.py` (wrapper que silencia stderr)
- **Severidade**: Nenhuma - não afetam funcionalidade

### WebEngine não carrega/falha ao renderizar
- Tente reexecutar — o app faz um auto-restart com flags seguras uma vez
- Se persistir: `$env:AMARELO_DISABLE_GPU = '1'; python main.py`
- Última tentativa: Instalar/atualizar `pip install -U PySide6 PySide6-QtWebEngine`

### Vídeos não aparecem embutidos, abrem no navegador
- Significa que `QWebEngineView` não está disponível ou falhou
- App continua funcionando com fallback (links abrem externamente)
- Instale `PySide6-QtWebEngine`: `pip install PySide6-QtWebEngine`

---

## Requisitos

- Python 3.9+
- PySide6 (inclui QtWebEngine)
- Windows 7+ (ou equivalente)
- Conexão com internet (para carregar playlists YouTube)

---

## Dicas de Uso

- **Salve seu projeto** (Ctrl+S) — playlists são salvas junto com o arquivo
- **Múltiplas mídias**: Você pode anexar vários objetos, cada um com sua própria playlist
- **Imagens**: Pode adicionar imagens (URLs ou locais) — aparecem embutidas
- **Áudio/Vídeo local**: Funciona melhor com formatos padrão (.mp3, .mp4, etc.)

---

**Última atualização**: Janeiro 2026
