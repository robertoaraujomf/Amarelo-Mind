#!/bin/bash
# Build script for Amarelo Mind - macOS
# Requires: Python 3, PyInstaller
set -e

APP_NAME="AmareloMind"
VERSION="1.5"
BUILD_DIR="dist/macos"

echo "Building ${APP_NAME} v${VERSION} for macOS..."

rm -rf dist build Output

pyinstaller --noconfirm \
    --name "${APP_NAME}" \
    --windowed \
    --icon assets/icons/App_icon.icns \
    --add-data "assets:assets" \
    --osx-bundle-identifier br.amarelo.mind \
    --target-arch arm64 \
    --target-arch x86_64 \
    run_amarelo.py

mkdir -p "${BUILD_DIR}"

cp -r "dist/${APP_NAME}.app" "${BUILD_DIR}/"

cat > "${BUILD_DIR}/install.sh" << 'INSTALL_EOF'
#!/bin/bash
# Amarelo Mind - macOS Installer
set -e

APP_NAME="AmareloMind.app"
INSTALL_DIR="/Applications"

echo "Installing Amarelo Mind..."

if [ -d "${INSTALL_DIR}/${APP_NAME}" ]; then
    echo "Removing previous installation..."
    rm -rf "${INSTALL_DIR}/${APP_NAME}"
fi

cp -r "$(dirname "$0")/${APP_NAME}" "${INSTALL_DIR}/"

# Register .amind file association
osascript -e '
tell application "System Events"
    set extList to {|.amind|:{|AmareloMind|:"Amarelo Mind File"}}
end tell
'

# Use duti (if available) or LSHandler to register
if command -v duti &> /dev/null; then
    duti -s br.amarelo.mind .amind all
else
    echo "Note: Install 'duti' (brew install duti) to register .amind file association."
    echo "Manual: Right-click a .amind file > Get Info > Open with > Amarelo Mind > Change All"
fi

echo "Amarelo Mind installed successfully!"
INSTALL_EOF
chmod +x "${BUILD_DIR}/install.sh"

echo "Done! macOS build at: ${BUILD_DIR}/${APP_NAME}.app"
