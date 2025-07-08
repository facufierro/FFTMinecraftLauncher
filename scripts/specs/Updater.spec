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
updater_dir = project_root / 'updater'
src_dir = updater_dir / 'src'
main_script = updater_dir / 'app.py'

print(f"Building Updater from: {updater_dir}")
print(f"Main script: {main_script}")

# Application metadata
APP_NAME = 'Updater'
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'GitHub-based App Updater'

# Data files to bundle (minimal for updater)
datas = []

# Core dependencies for simple updater
hiddenimports = [
    # GUI Framework (lightweight)
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    
    # HTTP and networking
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    
    # Standard library essentials
    'json',
    'logging',
    'threading',
    'subprocess',
    'pathlib',
    'datetime',
    'tempfile',
    'shutil',
    'zipfile',
    'hashlib',
    'argparse',
    'importlib.util',
    
    # System operations
    'os',
    'sys',
    'platform',
]

# Auto-discover updater modules
def collect_updater_modules():
    """Automatically collect all updater modules from src directory."""
    modules = []
    for py_file in src_dir.rglob('*.py'):
        if py_file.name != '__init__.py':
            # Convert to module path: src/models/app_updater.py -> src.models.app_updater
            relative = py_file.relative_to(updater_dir)
            module = str(relative.with_suffix('')).replace(os.sep, '.')
            modules.append(module)
    return modules

# Add discovered modules to hidden imports
hiddenimports.extend(collect_updater_modules())

# Build analysis
a = Analysis(
    [str(main_script)],
    pathex=[str(project_root), str(updater_dir), str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy libraries not needed for updater
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'customtkinter',  # Use basic tkinter instead
        'psutil',         # Not needed for updater
        
        # Testing frameworks
        'pytest',
        'unittest',
        'doctest',
        
        # Development tools
        'pdb',
        'cProfile',
        'profile',
        
        # Unix-specific modules
        'pwd',
        'grp',
        'termios',
        'fcntl',
        'resource',
        'readline',
        
        # Audio modules
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
    console=True,  # Show console for updater (useful for progress)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # No icon for updater
    icon=None,
    version_file=None,
    manifest=None,
    uac_admin=False,
    uac_uiaccess=False,
)

print(f"✓ Built {APP_NAME} v{APP_VERSION}")
print(f"✓ Executable: {APP_NAME}.exe")
print(f"✓ Console mode: enabled")
print(f"✓ Source modules: {len([m for m in hiddenimports if m.startswith('src.')])}")
print(f"✓ Total dependencies: {len(hiddenimports)}")
