#!/bin/bash
# Build script for Amarelo Mind
set -e

APP_NAME="amarelo-mind"
VERSION="1.2"
BUILD_DIR="build_deb"
PKG_DIR="${BUILD_DIR}/${APP_NAME}_${VERSION}"

echo "Building ${APP_NAME} v${VERSION}..."

# Clean previous builds
rm -rf ${BUILD_DIR}
rm -f *.deb

# Create directory structure
mkdir -p ${PKG_DIR}/usr/share/amarelo-mind
mkdir -p ${PKG_DIR}/usr/share/applications
mkdir -p ${PKG_DIR}/usr/share/icons/hicolor/48x48/apps
mkdir -p ${PKG_DIR}/DEBIAN

# Copy application files - Binary version
cp -r assets ${PKG_DIR}/usr/share/amarelo-mind/
cp dist/AmareloMind ${PKG_DIR}/usr/share/amarelo-mind/
chmod +x ${PKG_DIR}/usr/share/amarelo-mind/AmareloMind

# Copy icon
cp assets/icons/App_icon.png ${PKG_DIR}/usr/share/icons/hicolor/48x48/apps/amarelo-mind.png

# Create symlinks for easy execution
mkdir -p ${PKG_DIR}/usr/bin
ln -s /usr/share/amarelo-mind/AmareloMind ${PKG_DIR}/usr/bin/amarelo-mind
ln -s /usr/share/amarelo-mind/AmareloMind ${PKG_DIR}/usr/bin/AmareloMind

# Create desktop file
cat > ${PKG_DIR}/usr/share/applications/amarelo-mind.desktop << EOF
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=Amarelo Mind
Comment=Interactive Mind Mapping Tool with Dark Green Design
Exec=/usr/share/amarelo-mind/AmareloMind
Icon=amarelo-mind
Terminal=false
Categories=Office;Utility;
StartupWMClass=AmareloMind
EOF

# Create DEBIAN/control
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

# Create postinst
cat > ${PKG_DIR}/DEBIAN/postinst << 'EOF'
#!/bin/sh
set -e
case "$1" in
    configure)
        update-desktop-database 2>/dev/null || true
        ;;
esac
exit 0
EOF
chmod +x ${PKG_DIR}/DEBIAN/postinst

# Create prerm
cat > ${PKG_DIR}/DEBIAN/prerm << 'EOF'
#!/bin/sh
set -e
case "$1" in
    remove)
        ;;
esac
exit 0
EOF
chmod +x ${PKG_DIR}/DEBIAN/prerm

# Build package
dpkg-deb --build ${PKG_DIR}

echo "Done! Package: ${APP_NAME}_${VERSION}.deb"
ls -lh *.deb
