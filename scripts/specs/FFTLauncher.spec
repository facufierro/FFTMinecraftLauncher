# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FFT Minecraft Launcher
Optimized build configuration for Windows executable
"""

import sys
import os
from pathlib import Path

# Project structure
spec_dir = Path(SPEC).parent
project_root = spec_dir.parent.parent
launcher_dir = project_root / 'launcher'
src_dir = launcher_dir / 'src'
main_script = launcher_dir / 'app.py'

print(f"Building FFT Launcher from: {launcher_dir}")
print(f"Main script: {main_script}")

# Application metadata
APP_NAME = 'FFTLauncher'
APP_VERSION = '2.0.0'
APP_DESCRIPTION = 'FFT Minecraft Modpack Launcher'

# Data files to bundle
datas = [
    (str(project_root / 'assets' / 'icon.ico'), 'assets'),
]

# Core dependencies for CustomTkinter GUI application
hiddenimports = [
    # GUI Framework
    'customtkinter',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    
    # Image processing for CustomTkinter
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    
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
    'configparser',
    'tempfile',
    'shutil',
    'zipfile',
    'hashlib',
    'base64',
    'platform',
    'webbrowser',
    'queue',
    'concurrent.futures',
    
    # Type hints
    'typing',
    'dataclasses',
    'enum',
]

# Auto-discover source modules
def collect_source_modules():
    """Automatically collect all source modules from src directory."""
    modules = []
    for py_file in src_dir.rglob('*.py'):
        if py_file.name != '__init__.py':
            # Convert to module path: src/core/launcher.py -> src.core.launcher
            relative = py_file.relative_to(launcher_dir)
            module = str(relative.with_suffix('')).replace(os.sep, '.')
            modules.append(module)
    return modules

# Add discovered modules to hidden imports
hiddenimports.extend(collect_source_modules())

# Build analysis
a = Analysis(
    [str(main_script)],
    pathex=[str(project_root), str(launcher_dir), str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Testing frameworks
        'pytest',
        'unittest',
        'doctest',
        
        # Development tools
        'pdb',
        'cProfile',
        'profile',
        
        # System monitoring (not needed for launcher)
        'psutil',
        
        # Unix-specific modules (building for Windows)
        'pwd',
        'grp',
        'termios',
        'fcntl',
        'resource',
        'readline',
        
        # Audio modules not needed
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
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application - no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows executable options
    icon=str(project_root / 'assets' / 'icon.ico'),
    version_file=None,
    manifest=None,
    uac_admin=False,
    uac_uiaccess=False,
)

print(f"Built {APP_NAME} v{APP_VERSION}")
print(f"Executable: {APP_NAME}.exe")
print(f"Icon: {project_root / 'assets' / 'icon.ico'}")
print(f"Source modules: {len([m for m in hiddenimports if m.startswith('src.')])}")
print(f"Total dependencies: {len(hiddenimports)}")
