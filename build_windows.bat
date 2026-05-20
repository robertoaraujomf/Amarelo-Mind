@echo off
REM Build script for Amarelo Mind - Windows
REM Requires: Python 3, PyInstaller, Inno Setup (for .exe installer)

set APP_NAME=AmareloMind
set VERSION=1.5

echo Building %APP_NAME% v%VERSION% for Windows...

REM Clean previous builds
rmdir /s /q dist build Output 2>nul

REM Step 1: Build with PyInstaller
pyinstaller --noconfirm ^
    --name "%APP_NAME%" ^
    --windowed ^
    --icon assets\icons\App_icon.ico ^
    --add-data "assets;assets" ^
    run_amarelo.py

REM Step 2: Bundle necessary DLLs if needed
REM (PyInstaller handles most dependencies automatically)

REM Step 3: Create installer with Inno Setup
REM Requires Inno Setup installed at default location
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" script.iss
    echo Installer created at Output\AmareloMindSetup-%VERSION%.exe
) else (
    echo Inno Setup not found. Portable build at: dist\%APP_NAME%\
    echo Install Inno Setup from https://jrsoftware.org/isinfo.php to create installer
)

echo Done!
