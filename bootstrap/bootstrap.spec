# -*- mode: python ; coding: utf-8 -*-
import os

# Get absolute path to icon
ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(SPEC))), 'assets', 'minecraft_icon.ico')

# Debug: Print icon path
print(f"Icon path: {ICON_PATH}")
print(f"Icon exists: {os.path.exists(ICON_PATH)}")

a = Analysis(
    ['bootstrap.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
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
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
)
