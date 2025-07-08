# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FFT Minecraft Launcher
Builds the launcher into a standalone executable FFTLauncher.exe
"""

import sys
import os
from pathlib import Path

# Get the project root directory
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(spec_dir)  # Go up from scripts/specs to project root

# Add src directory to Python path
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

# Application metadata
app_name = 'FFTLauncher'
app_version = '2.0.0'
app_description = 'FFT Minecraft Modpack Launcher'
app_author = 'FFT Team'

# Define the main script
main_script = os.path.join(project_root, 'app.py')

# Data files to include
data_files = [
    # Include assets
    (os.path.join(project_root, 'assets', 'icon.ico'), 'assets'),
    # Include requirements (for reference)
    (os.path.join(project_root, 'requirements.txt'), '.'),
    (os.path.join(project_root, 'README.md'), '.'),
]

# Hidden imports that PyInstaller might miss
hidden_imports = [
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'requests',
    'zipfile',
    'json',
    'pathlib',
    'datetime',
    'threading',
    'subprocess',
    'shutil',
    'tempfile',
    'urllib.request',
    'urllib.parse',
    'logging',
    'configparser',
    'hashlib',
    'base64',
    'platform',
    'webbrowser',
    'typing',
    'dataclasses',
    'enum',
    'concurrent.futures',
    'queue',
]

# Collect all source modules
def collect_src_modules():
    """Collect all Python modules from the src directory."""
    modules = []
    src_path = Path(src_dir)
    
    for py_file in src_path.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        # Convert file path to module path
        rel_path = py_file.relative_to(src_path)
        module_path = str(rel_path.with_suffix('')).replace(os.sep, '.')
        modules.append(f'src.{module_path}')
    
    return modules

# Add all source modules to hidden imports
src_modules = collect_src_modules()
hidden_imports.extend(src_modules)

# Analysis configuration
a = Analysis(
    [main_script],
    pathex=[project_root, src_dir],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'unittest',
        'doctest',
        'pdb',
        'cProfile',
        'profile',
        'pstats',
        'trace',
        'timeit',
        'dis',
        'pickletools',
        'calendar',
        'email',
        'html',
        'http',
        'xmlrpc',
        'sqlite3',
        'turtle',
        'audioop',
        'chunk',
        'colorsys',
        'imghdr',
        'sndhdr',
        'sunau',
        'wave',
        'aifc',
        'ossaudiodev',
        'spwd',
        'grp',
        'pwd',
        'crypt',
        'termios',
        'tty',
        'pty',
        'fcntl',
        'pipes',
        'posixpath',
        'resource',
        'readline',
        'rlcompleter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX compression to reduce file size
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific options
    icon=os.path.join(project_root, 'assets', 'icon.ico'),
    version_file=None,  # We could create a version file if needed
    manifest=None,
    uac_admin=False,  # Don't require admin privileges
    uac_uiaccess=False,
)

# Additional build information
print(f"Building {app_name} v{app_version}")
print(f"Project root: {project_root}")
print(f"Main script: {main_script}")
print(f"Source directory: {src_dir}")
print(f"Hidden imports: {len(hidden_imports)} modules")
print(f"Data files: {len(data_files)} files")
