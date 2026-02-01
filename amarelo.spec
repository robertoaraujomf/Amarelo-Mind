# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Project base
project_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(project_dir, 'assets')

# Hidden imports to ensure Qt plugins are collected
hidden = []
hidden += collect_submodules('PySide6.QtMultimedia')
hidden += collect_submodules('PySide6.QtMultimediaWidgets')
hidden += collect_submodules('PySide6.QtWebEngineCore')
hidden += collect_submodules('PySide6.QtWebEngineWidgets')

# Data files: assets and any non-Python resources
datas = []
if os.path.isdir(assets_dir):
    datas.append((assets_dir, 'assets'))

# Include PySide6 Qt resources if needed (usually handled by hooks)
datas += collect_data_files('PySide6', include_py_files=False)

block_cipher = None

app = 'run_amarelo.py'

a = Analysis(
    [app],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='AmareloMind',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('assets', 'AmareloLogo.ico') if os.path.exists(os.path.join('assets','AmareloLogo.ico')) else None,
)
