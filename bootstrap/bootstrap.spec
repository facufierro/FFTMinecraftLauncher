# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for MINIMAL BOOTSTRAP
# This bootstrap is designed to be stable and never need rebuilding
# It only downloads the launcher package and launches it as a subprocess

import os

# Get absolute path to icon
ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(SPEC))), 'assets', 'icon.ico')

# Debug: Print icon path
print(f"Building MINIMAL BOOTSTRAP")
print(f"Icon path: {ICON_PATH}")
print(f"Icon exists: {os.path.exists(ICON_PATH)}")

a = Analysis(
    ['bootstrap.py'],
    pathex=[],
    binaries=[],
    datas=[],
    # Minimal imports - only what bootstrap needs
    hiddenimports=['requests', 'tkinter', 'zipfile'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy packages not needed by bootstrap
        'numpy', 'pandas', 'matplotlib', 'scipy',
        'PIL', 'pygame', 'opencv-python'
    ],
    noarchive=False,
    optimize=2,  # Higher optimization for minimal size
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FFTMinecraftLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Disable strip to avoid warnings on Windows
    upx=False,    # Disable UPX to avoid compatibility issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
)
