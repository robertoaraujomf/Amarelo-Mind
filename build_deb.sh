#!/bin/bash
set -e

APP_NAME="amarelo-mind"
VERSION="1.6.0"
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

        # Limpar ícones MIME de tamanhos antigos/inválidos em todos os temas
        for stale_size in 36 72 96 192 512; do
            rm -f "/usr/share/icons/hicolor/${stale_size}x${stale_size}/mimetypes/application-x-amind.png" 2>/dev/null || true
            rmdir "/usr/share/icons/hicolor/${stale_size}x${stale_size}/mimetypes" 2>/dev/null || true
        done
        for icon_dir in /usr/share/icons/*/; do
            theme=$(basename "$icon_dir")
            for stale_size in 36 72 96 192 512; do
                rm -f "${icon_dir}${stale_size}x${stale_size}/mimetypes/application-x-amind.png" 2>/dev/null || true
                rmdir "${icon_dir}${stale_size}x${stale_size}/mimetypes" 2>/dev/null || true
            done
        done

        # Copiar ícone MIME para hicolor + temas que declaram mimetypes no index.theme
        # Temas sem declaração mimetypes causam todos os tamanhos a usarem 16x16
        for icon_dir in /usr/share/icons/*/; do
            theme=$(basename "$icon_dir")
            if grep -q 'mimetypes' "${icon_dir}index.theme" 2>/dev/null; then
                for s in 16 22 24 32 48 64 128 256; do
                    mkdir -p "${icon_dir}${s}x${s}/mimetypes"
                    cp "/usr/share/icons/hicolor/${s}x${s}/mimetypes/application-x-amind.png" \
                       "${icon_dir}${s}x${s}/mimetypes/" 2>/dev/null || true
                done
                gtk-update-icon-cache -f "${icon_dir}" 2>/dev/null || true
            fi
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
