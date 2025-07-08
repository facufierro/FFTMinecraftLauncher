#!/usr/bin/env python3
"""
FFT Minecraft Launcher Build Script
Builds FFTLauncher.exe and Updater.exe executables using PyInstaller
"""

import argparse
import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any


class BuildScript:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.python_exe = self._find_python_executable()
        self.version = self._get_version()
        
    def _find_python_executable(self) -> str:
        """Find the Python executable in virtual environment."""
        possible_paths = [
            self.project_root / ".venv" / "Scripts" / "python.exe",
            self.project_root / "_env" / "Scripts" / "python.exe"
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"Using Python environment: {path}")
                return str(path)
        
        print("ERROR: No virtual environment found (.venv or _env)")
        sys.exit(1)
    
    def _get_version(self) -> str:
        """Get version from git tags."""
        try:
            result = subprocess.run(
                ["git", "tag", "--list", "--sort=-version:refname"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
                # Find first valid semantic version tag
                for tag in tags:
                    if tag.startswith('v') and len(tag.split('.')) == 3:
                        print(f"Using version: {tag}")
                        return tag
            
            print("Warning: No valid git tags found, using default version")
            return "v0.0.0"

        except Exception as e:
            print(f"Warning: Could not get git version: {e}")
            return "v0.0.0"
    
    def _update_config_version(self) -> None:
        """Update launcher_config.json with the current version."""
        try:
            import json
            
            config_file = self.project_root / "launcher" / "launcher_config.json"
            version_clean = self.version.lstrip('v')  # Remove 'v' prefix if present
            
            if config_file.exists():
                # Read existing config
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Update launcher version
                config_data['launcher_version'] = version_clean
                
                # Write back to file
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                
                print(f"Updated launcher version in config: {config_file} ({version_clean})")
            else:
                print(f"Warning: Config file not found: {config_file}")
            
        except Exception as e:
            print(f"Warning: Could not update launcher version in config: {e}")
    
    def _update_launcher_version_constant(self) -> None:
        """Update the LAUNCHER_VERSION constant in launcher.py before building."""
        try:
            launcher_file = self.project_root / "launcher" / "src" / "core" / "launcher.py"
            version_clean = self.version.lstrip('v')  # Remove 'v' prefix if present
            
            if launcher_file.exists():
                # Read the current file
                with open(launcher_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace the version constant
                import re
                new_content = re.sub(
                    r'LAUNCHER_VERSION = "[^"]*"',
                    f'LAUNCHER_VERSION = "{version_clean}"',
                    content
                )
                
                # Write back to file
                with open(launcher_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"Updated LAUNCHER_VERSION constant to: {version_clean}")
            else:
                print(f"Warning: Launcher file not found: {launcher_file}")
            
        except Exception as e:
            print(f"Warning: Could not update launcher version constant: {e}")
    
    def _check_pyinstaller(self) -> bool:
        """Check if PyInstaller is installed, install if needed."""
        try:
            result = subprocess.run(
                [self.python_exe, "-c", "import PyInstaller; print('PyInstaller found')"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("PyInstaller found")
                return True
            else:
                print("PyInstaller not found. Installing...")
                install_result = subprocess.run(
                    [self.python_exe, "-m", "pip", "install", "pyinstaller"],
                    cwd=self.project_root
                )
                return install_result.returncode == 0
                
        except Exception as e:
            print(f"Error checking PyInstaller: {e}")
            return False
    
    def clean_build_cache(self) -> None:
        """Clean build cache directories."""
        print("Cleaning build cache...")
        
        dirs_to_clean = [
            self.project_root / "build",
            self.project_root / "dist"
        ]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  Removed: {dir_path}")
    
    def build_application(self, app_name: str, spec_file: str, expected_exe: str, description: str) -> bool:
        """Build a single application using PyInstaller."""
        print(f"\nBuilding {app_name}...")
        print(f"Using spec file: {spec_file}")
        
        spec_path = self.project_root / spec_file
        if not spec_path.exists():
            print(f"ERROR: Spec file not found at {spec_path}")
            return False
        
        print("  Running PyInstaller...")
        print(f"  Command: {self.python_exe} -m PyInstaller {spec_file} --noconfirm --clean")
        
        try:
            # Change to project root for PyInstaller
            result = subprocess.run(
                [self.python_exe, "-m", "PyInstaller", str(spec_file), "--noconfirm", "--clean"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Show PyInstaller output (last 10 lines for brevity)
            if result.stdout:
                lines = result.stdout.split('\n')
                print("  PyInstaller output (last 10 lines):")
                for line in lines[-10:]:
                    if line.strip():
                        print(f"    {line}")
            
            if result.stderr:
                print("  PyInstaller errors:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        print(f"    {line}")
            
            # Check if executable was created
            time.sleep(0.5)  # Brief pause for file system
            exe_path = self.project_root / expected_exe
            
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"✓ {app_name} built successfully")
                print(f"  File: {exe_path}")
                print(f"  Size: {file_size:.2f} MB")
                return True
            else:
                print(f"✗ {app_name} build failed")
                print(f"  PyInstaller exit code: {result.returncode}")
                print(f"  Expected executable: {exe_path}")
                return False
                
        except Exception as e:
            print(f"ERROR: Exception during {app_name} build: {e}")
            return False
    
    def build_all(self, target: str, clean: bool) -> None:
        """Build all or specific applications."""
        print("Building FFT Applications...")
        print("=" * 30)
        
        # Change to project root
        os.chdir(self.project_root)
        print(f"Working directory: {self.project_root}")
        
        # Clean if requested
        if clean:
            self.clean_build_cache()
        
        print(f"Version: {self.version}")
        
        # Update launcher_config.json with current version
        self._update_config_version()
        
        # Update launcher version constant before building
        self._update_launcher_version_constant()
        
        # Check PyInstaller
        if not self._check_pyinstaller():
            print("ERROR: Failed to install PyInstaller")
            sys.exit(1)
        
        # Build applications
        build_results = []
        
        # Build Launcher
        if target in ["launcher", "all"]:
            success = self.build_application(
                "FFT Launcher",
                "scripts/specs/FFTLauncher.spec",
                "dist/FFTLauncher.exe",
                "Main Minecraft launcher"
            )
            build_results.append({
                "name": "FFT Launcher",
                "success": success,
                "path": "dist/FFTLauncher.exe"
            })
        
        # Build Updater
        if target in ["updater", "all"]:
            success = self.build_application(
                "Updater",
                "scripts/specs/Updater.spec", 
                "dist/Updater.exe",
                "GitHub-based app updater"
            )
            build_results.append({
                "name": "Updater",
                "success": success,
                "path": "dist/Updater.exe"
            })
        
        # Summary
        print("\n" + "=" * 40)
        print("BUILD SUMMARY")
        print("=" * 40)
        
        all_successful = True
        for result in build_results:
            if result["success"]:
                print(f"✓ {result['name']}: SUCCESS")
                exe_path = self.project_root / result["path"]
                if exe_path.exists():
                    file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                    print(f"  Size: {file_size:.2f} MB")
            else:
                print(f"✗ {result['name']}: FAILED")
                all_successful = False
        
        print(f"\nVersion: {self.version}")
        
        if all_successful:
            print("All builds completed successfully!")
        else:
            print("Some builds failed - check the output above")
            sys.exit(1)
        
        print("=" * 40)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build FFT Applications")
    parser.add_argument(
        "--target",
        choices=["launcher", "updater", "all"],
        default="all",
        help="Target to build (default: all)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build cache before building"
    )
    
    args = parser.parse_args()
    
    builder = BuildScript()
    builder.build_all(args.target, args.clean)


if __name__ == "__main__":
    main()
