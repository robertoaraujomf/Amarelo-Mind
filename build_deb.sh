#!/bin/bash
set -e

APP_NAME="amarelo-mind"
VERSION="1.6.4"
BUILD_DIR="build_deb"
PKG_DIR="${BUILD_DIR}/${APP_NAME}_${VERSION}"

echo "Building ${APP_NAME} v${VERSION}..."

rm -rf ${BUILD_DIR}
rm -f *.deb
rm -rf dist build

pyinstaller amarelo.spec 2>&1

mkdir -p ${PKG_DIR}/usr/share/amarelo-mind
mkdir -p ${PKG_DIR}/usr/share/applications
mkdir -p ${PKG_DIR}/usr/share/icons/hicolor/48x48/apps
mkdir -p ${PKG_DIR}/usr/share/mime/packages
mkdir -p ${PKG_DIR}/DEBIAN

cp -r assets ${PKG_DIR}/usr/share/amarelo-mind/
cp dist/AmareloMind ${PKG_DIR}/usr/share/amarelo-mind/AmareloMind
chmod +x ${PKG_DIR}/usr/share/amarelo-mind/AmareloMind

cp assets/icons/App_icon.png ${PKG_DIR}/usr/share/icons/hicolor/48x48/apps/amarelo-mind.png

# Copy MIME type icon for .amind files — generate each size from source
python3 -c "
import sys, os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
app = QApplication(sys.argv)
src = QImage('assets/icons/Arquivos.png')

# Auto-crop: find bounding box of non-transparent content
w, h = src.width(), src.height()
left, top, right, bottom = w, h, 0, 0
for y in range(h):
    for x in range(w):
        if src.pixelColor(x, y).alpha() > 10:
            left = min(left, x)
            top = min(top, y)
            right = max(right, x)
            bottom = max(bottom, y)
trimmed = src.copy(left, top, right - left + 1, bottom - top + 1)

# Downscale once per target size using high-quality (Antialiasing + SmoothPixmap)
# painting, which produces smooth, non-pixelated edges (no alpha thresholding).
for s in [16, 22, 24, 32, 48, 64, 128, 256]:
    d = f'${PKG_DIR}/usr/share/icons/hicolor/{s}x{s}/mimetypes'
    os.makedirs(d, exist_ok=True)
    pix = QPixmap.fromImage(trimmed)
    out = QPixmap(s, s)
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    p.setRenderHint(QPainter.Antialiasing, True)
    # Fit while keeping aspect ratio, centered
    scaled = pix.scaled(s, s, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    x = (s - scaled.width()) // 2
    y = (s - scaled.height()) // 2
    p.drawPixmap(x, y, scaled)
    p.end()
    out.toImage().save(f'{d}/application-x-amind.png')

# O resolvedor de ícones (gtk_icon_theme_lookup_by_gicon, usado pelo Nemo) busca a
# lista de nomes [application-x-amind, application-x-generic, ...] tema a tema.
# Como o tema 'Adwaita' é SEMPRE pesquisado antes do hicolor e contém o icone
# generico, o fallback generico vencia antes de chegar ao hicolor. Solucao:
# fornecer um SVG escalavel do .amind no proprio Adwaita (que declara
# 'scalable/mimetypes'), garantindo o icon em qualquer tamanho, para qualquer tema.
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
import base64 as _b64

def _svg_for(icon, size=512):
    # centraliza em canvas 512 com o conteudo em alta resolucao
    canvas = QImage(size, size, QImage.Format_ARGB32)
    canvas.fill(Qt.transparent)
    p = QPainter(canvas)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    scaled = icon.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2
    p.drawImage(x, y, scaled)
    p.end()
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    canvas.save(buf, 'PNG')
    b64 = _b64.b64encode(bytes(ba)).decode()
    return (f'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{size}\" height=\"{size}\" '
            f'viewBox=\"0 0 {size} {size}\"><image width=\"{size}\" height=\"{size}\" '
            f'href=\"data:image/png;base64,{b64}\"/></svg>\\n')

svg_str = _svg_for(QPixmap.fromImage(trimmed).toImage())
docker = '${PKG_DIR}/usr/share/amarelo-mind/icons_mime'
os.makedirs(docker, exist_ok=True)
open(docker + '/application-x-amind.svg', 'w').write(svg_str)

# instalar tambem dentro do tema Adwaita (sempre presente na cadeia de temas)
adw_svg_dir = '${PKG_DIR}/usr/share/icons/Adwaita/scalable/mimetypes'
adw_png_dir = '${PKG_DIR}/usr/share/icons/Adwaita/16x16/mimetypes'
os.makedirs(adw_svg_dir, exist_ok=True)
os.makedirs(adw_png_dir, exist_ok=True)
open(f'{adw_svg_dir}/application-x-amind.svg', 'w').write(svg_str)
import shutil
corner = '${PKG_DIR}/usr/share/icons/hicolor/16x16/mimetypes/application-x-amind.png'
shutil.copyfile(corner, f'{adw_png_dir}/application-x-amind.png')
" 2>&1

mkdir -p ${PKG_DIR}/usr/bin
ln -s /usr/share/amarelo-mind/AmareloMind ${PKG_DIR}/usr/bin/amarelo-mind
ln -s /usr/share/amarelo-mind/AmareloMind ${PKG_DIR}/usr/bin/AmareloMind

cat > ${PKG_DIR}/usr/share/applications/amarelo-mind.desktop << EOF
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=Amarelo Mind
Comment=Interactive Mind Mapping Tool with Dark Green Design
Exec=/usr/share/amarelo-mind/AmareloMind %f
Icon=amarelo-mind
Terminal=false
Categories=Office;Utility;
MimeType=application/x-amind;
StartupNotify=false
StartupWMClass=AmareloMind
EOF

cat > ${PKG_DIR}/usr/share/mime/packages/amarelo-mind.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-amind">
    <comment>Amarelo Mind Map</comment>
    <glob pattern="*.amind"/>
    <icon name="application-x-amind"/>
  </mime-type>
</mime-info>
EOF

cat > ${PKG_DIR}/DEBIAN/control << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: office
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.34), libstdc++6, libglib2.0-0 (>= 2.68), libdbus-1-3, libxcb1, libxkbcommon0, libfontconfig1, libfreetype6
Maintainer: Amarelo Team <team@amarelo.br>
Description: Interactive Mind Mapping Tool
 A visual mind mapping application for creating and organizing ideas.
 Features dark green design, intuitive icons, and advanced node management.
EOF

cat > ${PKG_DIR}/DEBIAN/postinst << 'POSTINST'
#!/bin/sh
set -e
case "$1" in
    configure)
        update-desktop-database || true
        update-mime-database /usr/share/mime || true

        for user_home in /home/* /root; do
            [ -d "$user_home" ] || continue
            [ -d "$user_home/.config" ] || continue
            mimeapps="$user_home/.config/mimeapps.list"

            if [ ! -f "$mimeapps" ]; then
                mkdir -p "$user_home/.config"
                printf '[Added Associations]\n[Default Applications]\n' > "$mimeapps"
            fi

            if ! grep -q '^\[Default Applications\]' "$mimeapps" 2>/dev/null; then
                printf '\n[Default Applications]\n' >> "$mimeapps"
            fi

            sed -i '/^application\/x-amind=/d' "$mimeapps" 2>/dev/null || true
            sed -i '/^\[Default Applications\]/a application/x-amind=amarelo-mind.desktop' "$mimeapps" 2>/dev/null || true

            rm -f "$user_home/.local/share/applications/amarelo-mind.desktop" 2>/dev/null || true
            rm -f "$user_home/.local/share/applications/AmareloMind.desktop" 2>/dev/null || true
            rm -f "$user_home/.local/share/applications/mimeinfo.cache" 2>/dev/null || true
        done

        # Remover cópias antigas do ícone MIME de TODOS os temas, exceto hicolor
        # e Adwaita. Copiar o ícone para os temas "sombreava" o conjunto completo
        # de tamanhos do hicolor: o resolvedor de ícones (GTK) encontrava uma
        # cópia parcial (ex.: só 16x16) no tema ativo e nunca caía no hicolor,
        # exibindo o ícone 16x16 escalado (qualidade baixa) em qualquer tamanho.
        # O tema Adwaita é preservado pois é pesquisado SEMPRE antes do hicolor e
        # mantém o SVG escalável do .amind (senão o fallback 'application-x-generic'
        # do próprio Adwaita venceria e nenhum arquivo .amind mostraria o ícone).
        for icon_dir in /usr/share/icons/*/; do
            theme=$(basename "$icon_dir")
            [ "$theme" = "hicolor" -o "$theme" = "Adwaita" ] && continue
            rm -f "${icon_dir}"*/mimetypes/application-x-amind.png 2>/dev/null || true
        done
        for stale_size in 36 72 96 192 512; do
            rm -f "/usr/share/icons/hicolor/${stale_size}x${stale_size}/mimetypes/application-x-amind.png" 2>/dev/null || true
        done

        # Garantir o ícone no tema Adwaita (SVG escalável + PNG 16px)
        if [ -d "/usr/share/icons/Adwaita" ]; then
            mkdir -p /usr/share/icons/Adwaita/scalable/mimetypes \
                     /usr/share/icons/Adwaita/16x16/mimetypes
            cp -f /usr/share/amarelo-mind/icons_mime/application-x-amind.svg \
                  /usr/share/icons/Adwaita/scalable/mimetypes/ 2>/dev/null || true
            cp -f /usr/share/icons/hicolor/16x16/mimetypes/application-x-amind.png \
                  /usr/share/icons/Adwaita/16x16/mimetypes/ 2>/dev/null || true
            if [ -d /usr/share/icons/gnome ]; then
                mkdir -p /usr/share/icons/gnome/scalable/mimetypes
                cp -f /usr/share/amarelo-mind/icons_mime/application-x-amind.svg \
                      /usr/share/icons/gnome/scalable/mimetypes/ 2>/dev/null || true
            fi
        fi

        # Reconstruir os caches dos temas (incluindo os que não declaram 'mimetypes'
        # no index.theme, como o Mint-Y-Purple).
        for icon_dir in /usr/share/icons/*/; do
            [ -f "${icon_dir}index.theme" ] || continue
            gtk-update-icon-cache -f "${icon_dir}" 2>/dev/null || true
        done

        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database /usr/share/applications 2>/dev/null || true
        fi
        ;;
esac
exit 0
POSTINST
chmod +x ${PKG_DIR}/DEBIAN/postinst

cat > ${PKG_DIR}/DEBIAN/postrm << 'EOF'
#!/bin/sh
set -e
case "$1" in
    purge)
        rm -f /usr/share/mime/packages/amarelo-mind.xml
        update-mime-database /usr/share/mime || true
        update-desktop-database || true
        rm -f /usr/share/icons/hicolor/*/mimetypes/application-x-amind.png
        rm -f /usr/share/icons/Adwaita/scalable/mimetypes/application-x-amind.svg
        rm -f /usr/share/icons/Adwaita/16x16/mimetypes/application-x-amind.png
        rm -f /usr/share/icons/gnome/scalable/mimetypes/application-x-amind.svg
        rm -rf /usr/share/amarelo-mind/icons_mime
        for stale_size in 36 72 96 192 512; do
            rmdir "/usr/share/icons/hicolor/${stale_size}x${stale_size}/mimetypes" 2>/dev/null || true
        done
        active_theme=$(gsettings get org.cinnamon.desktop.interface icon-theme 2>/dev/null || \
                       gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null || echo "")
        active_theme=$(echo "$active_theme" | tr -d "'")
        if [ -n "$active_theme" ]; then
            rm -f "/usr/share/icons/$active_theme"/*/mimetypes/application-x-amind.png 2>/dev/null || true
        fi
        gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
        gtk-update-icon-cache /usr/share/icons/Adwaita 2>/dev/null || true
        ;;
    remove|upgrade|disappear)
        ;;
esac
exit 0
EOF
chmod +x ${PKG_DIR}/DEBIAN/postrm

cat > ${PKG_DIR}/DEBIAN/prerm << 'EOF'
#!/bin/sh
set -e
case "$1" in
    remove|upgrade|deconfigure)
        update-desktop-database || true
        update-mime-database /usr/share/mime || true
        ;;
esac
exit 0
EOF
chmod +x ${PKG_DIR}/DEBIAN/prerm

dpkg-deb --build ${PKG_DIR}

echo "Done! Package: ${PKG_DIR}.deb"
ls -lh ${PKG_DIR}.deb
