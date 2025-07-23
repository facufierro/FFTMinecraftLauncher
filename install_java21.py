#!/usr/bin/env python3
"""
Script to download and install Java 21 for Minecraft compatibility.
This script downloads OpenJDK 21 from Eclipse Adoptium (Temurin).
"""

import os
import sys
import requests
import subprocess
import platform
from pathlib import Path

def download_java21():
    """Download and install Java 21 for Windows"""
    if platform.system() != "Windows":
        print("This script currently only supports Windows. Please install Java 21 manually.")
        return False
    
    # Eclipse Adoptium (Temurin) download URL for Java 21 Windows x64
    java21_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_windows_hotspot_21.0.5_11.msi"
    
    print("Downloading Java 21 from Eclipse Adoptium...")
    print(f"URL: {java21_url}")
    
    try:
        # Download the installer
        response = requests.get(java21_url, stream=True)
        response.raise_for_status()
        
        installer_path = Path("OpenJDK21_installer.msi")
        
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded Java 21 installer to: {installer_path}")
        print("\nRunning installer...")
        
        # Run the MSI installer
        result = subprocess.run([
            "msiexec", "/i", str(installer_path), "/quiet", "/norestart"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Java 21 installed successfully!")
            
            # Clean up installer
            installer_path.unlink()
            
            # Try to find the installed Java
            java_paths = [
                "C:\\Program Files\\Eclipse Adoptium\\jdk-21*\\bin\\java.exe",
                "C:\\Program Files\\OpenJDK\\jdk-21*\\bin\\java.exe",
            ]
            
            import glob
            for path_pattern in java_paths:
                matches = glob.glob(path_pattern)
                if matches:
                    java_path = matches[0]
                    print(f"Java 21 found at: {java_path}")
                    
                    # Test the installation
                    test_result = subprocess.run([java_path, "-version"], capture_output=True, text=True)
                    if test_result.returncode == 0:
                        print("Java 21 installation verified!")
                        print(test_result.stderr)
                        return True
            
            print("Java 21 installed but could not verify installation automatically.")
            return True
            
        else:
            print(f"Installation failed with return code: {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
            
    except requests.RequestException as e:
        print(f"Failed to download Java 21: {e}")
        return False
    except Exception as e:
        print(f"Error during installation: {e}")
        return False

def check_current_java():
    """Check the current Java version"""
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Current Java version:")
            print(result.stderr)
            
            # Check if it's compatible (Java 17 or 21)
            import re
            version_match = re.search(r'"(\d+)\.', result.stderr)
            if version_match:
                major_version = int(version_match.group(1))
                if major_version in [17, 21]:
                    print(f"✓ Java {major_version} is compatible with Minecraft 1.21.1")
                    return True
                else:
                    print(f"✗ Java {major_version} is not compatible. Minecraft 1.21.1 needs Java 17 or 21.")
                    return False
            
        return False
    except FileNotFoundError:
        print("Java not found in PATH")
        return False

def main():
    print("Java 21 Installer for Minecraft Compatibility")
    print("=" * 50)
    
    print("\nChecking current Java installation...")
    if check_current_java():
        response = input("\nYou already have a compatible Java version. Do you still want to install Java 21? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            return
    
    print("\nWARNING: This will download and install Java 21 on your system.")
    print("Make sure you have administrator privileges.")
    response = input("Do you want to continue? (y/N): ")
    
    if response.lower() != 'y':
        print("Installation cancelled.")
        return
    
    if download_java21():
        print("\n" + "=" * 50)
        print("Java 21 installation completed!")
        print("\nIMPORTANT: You may need to:")
        print("1. Restart your command prompt/terminal")
        print("2. Update your JAVA_HOME environment variable")
        print("3. Or the launcher will automatically detect Java 21")
        print("\nYou can now run your Minecraft launcher.")
    else:
        print("\nInstallation failed. Please install Java 21 manually from:")
        print("https://adoptium.net/temurin/releases/?version=21")

if __name__ == "__main__":
    main()
