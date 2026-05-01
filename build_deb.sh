#!/bin/bash
# Build script for Amarelo Mind
set -e

APP_NAME="amarelo-mind"
VERSION="1.1"
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

# Copy application files
cp -r *.py ${PKG_DIR}/usr/share/amarelo-mind/
cp -r assets ${PKG_DIR}/usr/share/amarelo-mind/
cp -r items ${PKG_DIR}/usr/share/amarelo-mind/
cp -r core ${PKG_DIR}/usr/share/amarelo-mind/
cp -r debian ${PKG_DIR}/usr/share/amarelo-mind/
cp amarelo.spec ${PKG_DIR}/usr/share/amarelo-mind/ 2>/dev/null || true
cp AmareloMind.spec ${PKG_DIR}/usr/share/amarelo-mind/ 2>/dev/null || true

# Copy icon
cp assets/icons/App_icon.png ${PKG_DIR}/usr/share/icons/hicolor/48x48/apps/amarelo-mind.png

# Create launcher script
cat > ${PKG_DIR}/usr/share/amarelo-mind/run_amarelo.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Set base directory
base_dir = "/usr/share/amarelo-mind"

# Suppress WebEngine warnings
os.environ.setdefault("QT_LOGGING_RULES", 
    "qt.webengine.*=false;qt.qpa.gl=false;js.*=false;*doh*=false")

# Add to path
sys.path.insert(0, base_dir)

# Set icon path
os.environ["AMarelo_ICON_PATH"] = os.path.join(base_dir, "assets", "icons", "App_icon.ico")

# Import and run
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import main

app = QApplication(sys.argv)
app.setApplicationName("AmareloMind")
app.setApplicationDisplayName("Amarelo Mind")

icon_path = os.path.join(base_dir, "assets", "icons", "App_icon.ico")
if os.path.exists(icon_path):
    app.setWindowIcon(QIcon(icon_path))

window = main.AmareloMainWindow()
window.show()
sys.exit(app.exec())
EOF

chmod +x ${PKG_DIR}/usr/share/amarelo-mind/run_amarelo.py

# Create desktop file
cat > ${PKG_DIR}/usr/share/applications/amarelo-mind.desktop << EOF
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=Amarelo Mind
Comment=Interactive Mind Mapping Tool
Exec=/usr/share/amarelo-mind/run_amarelo.py
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
Depends: python3, python3-pyside6, libc6 (>= 2.31)
Maintainer: Amarelo Team <team@amarelo.br>
Description: Interactive Mind Mapping Tool
 A visual mind mapping application for creating and organizing ideas.
 Supports text nodes, connections, media embedding, and more.
EOF

# Create postinst
cat > ${PKG_DIR}/DEBIAN/postinst << 'EOF'
#!/bin/sh
set -e
case "$1" in
    configure)
        update-alternatives --install /usr/bin/amarelo-mind amarelo-mind /usr/share/amarelo-mind/run_amarelo.py 100 2>/dev/null || true
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
        update-alternatives --remove amarelo-mind /usr/share/amarelo-mind/run_amarelo.py 2>/dev/null || true
        ;;
esac
exit 0
EOF
chmod +x ${PKG_DIR}/DEBIAN/prerm

# Build package
dpkg-deb --build ${PKG_DIR}

echo "Done! Package: ${APP_NAME}_${VERSION}.deb"
ls -lh *.deb
