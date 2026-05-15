#!/bin/bash
# Cross-platform build script for Amarelo Mind
set -e

VERSION="1.3"
echo "=========================================="
echo " Amarelo Mind v${VERSION} - Multi-Platform Build"
echo "=========================================="

case "$(uname -s)" in
    Linux*)
        echo "Building for Linux..."

        # Step 1: Build binary with PyInstaller
        echo ">> Building binary..."
        pyinstaller --noconfirm \
            --name AmareloMind \
            --windowed \
            --icon assets/icons/App_icon.png \
            --add-data "assets:assets" \
            run_amarelo.py

        # Step 2: Build .deb package
        echo ">> Building .deb package..."
        bash build_deb.sh

        echo ">> Done! Linux .deb package created."
        ;;
    Darwin*)
        echo "Building for macOS..."

        # Generate .icns from .png if needed
        if [ ! -f "assets/icons/App_icon.icns" ]; then
            mkdir -p App_icon.iconset
            for size in 16 32 64 128 256 512 1024; do
                sips -z $size $size "assets/icons/App_icon.png" \
                    --out "App_icon.iconset/icon_${size}x${size}.png" 2>/dev/null
                half=$((size / 2))
                sips -z $size $size "assets/icons/App_icon.png" \
                    --out "App_icon.iconset/icon_${half}x${half}@2x.png" 2>/dev/null
            done
            iconutil -c icns App_icon.iconset
            mv App_icon.icns "assets/icons/App_icon.icns"
            rm -rf App_icon.iconset
        fi

        # Build with PyInstaller
        pyinstaller --noconfirm \
            --name AmareloMind \
            --windowed \
            --icon assets/icons/App_icon.icns \
            --add-data "assets:assets" \
            --osx-bundle-identifier br.amarelo.mind \
            run_amarelo.py

        # Create .dmg (requires create-dmg or similar)
        echo ">> Creating .dmg..."
        mkdir -p dist/macos
        cp -r "dist/AmareloMind.app" "dist/macos/"
        if command -v create-dmg &> /dev/null; then
            create-dmg \
                --volname "Amarelo Mind" \
                --window-pos 200 120 \
                --window-size 600 300 \
                --icon-size 100 \
                --icon "AmareloMind.app" 175 120 \
                --app-drop-link 425 120 \
                "dist/AmareloMind-${VERSION}.dmg" \
                "dist/macos/"
        else
            echo "Note: Install 'create-dmg' (brew install create-dmg) to create .dmg"
            echo "App bundle ready at: dist/macos/AmareloMind.app"
        fi
        echo ">> Done! macOS build created."
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Building for Windows..."
        cmd.exe /c build_windows.bat
        echo ">> Done! Windows build created."
        ;;
    *)
        echo "Unsupported OS: $(uname -s)"
        exit 1
        ;;
esac
