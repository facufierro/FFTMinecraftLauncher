# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for GitHub-based App Updater
Simple, lightweight updater executable
"""

import sys
import os
from pathlib import Path

# Project structure
spec_dir = Path(SPEC).parent
project_root = spec_dir.parent.parent

# Use the correct updater script path
main_script = project_root / 'src' / 'tools' / 'updater.py'

print(f"Building Simple Updater from: {main_script}")

# Application metadata
APP_NAME = 'Updater'
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'Simple File Replacement Updater'

# Data files to bundle (none needed for simple updater)
datas = []

# Minimal dependencies for simple updater
hiddenimports = [
    # Standard library essentials only
    'os',
    'sys',
    'subprocess',
    'tkinter',
    'tkinter.ttk',
]

# No auto-discovery needed for simple updater
# hiddenimports already contains everything we need

# Build analysis
    a = Analysis(
    [str(main_script)],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude everything we don't need
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'customtkinter',
        'requests',
        'urllib3',
        'psutil',
        'pytest',
        'unittest',
        'doctest',
        'pdb',
        'cProfile',
        'profile',
        'pwd',
        'grp',
        'termios',
        'fcntl',
        'resource',
        'readline',
        'audioop',
        'wave',
        'sunau',
        'aifc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Create Python archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Build executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX for smaller size
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console - updater runs silently in background
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Use generic Windows executable icon
    icon=None,
    version_file=None,
    manifest=None,
    uac_admin=False,
    uac_uiaccess=False,
)

print(f"Built {APP_NAME} v{APP_VERSION}")
print(f"Executable: {APP_NAME}.exe")
print(f"Console mode: disabled")
print(f"Simple file replacement updater - minimal dependencies")
