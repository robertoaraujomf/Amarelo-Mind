#!/bin/bash
set -e

APP_NAME="amarelo-mind"
VERSION="1.5"
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

# Copy MIME type icon for .amind files to all standard sizes
for size in 16 24 32 48 64 128 256; do
    mkdir -p ${PKG_DIR}/usr/share/icons/hicolor/${size}x${size}/mimetypes
    cp assets/icons/files_amind_icon.png ${PKG_DIR}/usr/share/icons/hicolor/${size}x${size}/mimetypes/application-x-amind.png
done

mkdir -p ${PKG_DIR}/usr/bin
ln -s /usr/share/amarelo-mind/AmareloMind ${PKG_DIR}/usr/bin/amarelo-mind
ln -s /usr/share/amarelo-mind/AmareloMind ${PKG_DIR}/usr/bin/AmareloMind

cat > ${PKG_DIR}/usr/share/applications/amarelo-mind.desktop << EOF
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=Amarelo Mind
Comment=Interactive Mind Mapping Tool with Dark Green Design
Exec=env QT_NO_PORTAL=1 /usr/share/amarelo-mind/AmareloMind -name amarelo-mind %f
Icon=amarelo-mind
Terminal=false
Categories=Office;Utility;
MimeType=application/x-amind;
StartupNotify=false
StartupWMClass=amarelo-mind
EOF

cat > ${PKG_DIR}/usr/share/mime/packages/amarelo-mind.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-amind">
    <comment>Amarelo Mind Map</comment>
    <glob pattern="*.amind"/>
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

cat > ${PKG_DIR}/DEBIAN/postinst << 'EOF'
#!/bin/sh
set -e
case "$1" in
    configure)
        update-desktop-database || true
        update-mime-database /usr/share/mime || true
        xdg-mime default amarelo-mind.desktop application/x-amind || true

        for user_home in /home/* /root; do
            [ -d "$user_home" ] || continue
            mimeapps="$user_home/.config/mimeapps.list"
            if [ -f "$mimeapps" ]; then
                sed -i '/^application\/x-amind=/d' "$mimeapps" 2>/dev/null || true
            fi
            rm -f "$user_home/.local/share/applications/amarelo-mind.desktop" 2>/dev/null || true
            rm -f "$user_home/.local/share/applications/AmareloMind.desktop" 2>/dev/null || true
            rm -f "$user_home/.local/share/applications/mimeinfo.cache" 2>/dev/null || true
        done

        gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true

        active_theme=$(gsettings get org.cinnamon.desktop.interface icon-theme 2>/dev/null || \
                       gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null || echo "")
        active_theme=$(echo "$active_theme" | tr -d "'")
        [ -n "$active_theme" ] && [ -d "/usr/share/icons/$active_theme" ] || active_theme=""
        for theme in $active_theme hicolor; do
            [ -d "/usr/share/icons/$theme" ] || continue
            for size_dir in /usr/share/icons/$theme/*/mimetypes/; do
                [ -d "$size_dir" ] || continue
                cp /usr/share/icons/hicolor/48x48/mimetypes/application-x-amind.png \
                   "$size_dir/application-x-amind.png" 2>/dev/null || true
            done
            gtk-update-icon-cache -f "/usr/share/icons/$theme" 2>/dev/null || true
        done
        ;;
esac
exit 0
EOF
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
