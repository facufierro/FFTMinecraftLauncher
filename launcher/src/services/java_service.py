"""Simple portable Java service for the FFT Minecraft Launcher."""

import os
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional
from ..utils.logging_utils import get_logger


class JavaService:
    """Manages portable Java installation for the launcher."""
    
    def __init__(self):
        self.logger = get_logger()
        self.java_dir = Path.cwd() / "java"
        self.java_exe = self.java_dir / "bin" / "java.exe"
        
    def get_java_executable(self) -> Optional[str]:
        """Get Java executable path, downloading if needed."""
        # Check if portable Java already exists
        if self.java_exe.exists():
            if self._verify_java(str(self.java_exe)):
                return str(self.java_exe)
        
        # Try to download portable Java
        if self._download_portable_java():
            return str(self.java_exe)
            
        return None
    
    def _verify_java(self, java_path: str) -> bool:
        """Verify Java installation works."""
        try:
            result = subprocess.run([java_path, "-version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _download_portable_java(self) -> bool:
        """Download and extract portable Java 21."""
        try:
            self.logger.info("Downloading portable Java 21...")
            
            # Adoptium OpenJDK 21 portable for Windows x64
            java_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jre_x64_windows_hotspot_21.0.4_7.zip"
            zip_path = Path.cwd() / "temp" / "java21.zip"
            
            # Create temp directory
            zip_path.parent.mkdir(exist_ok=True)
            
            # Download
            urllib.request.urlretrieve(java_url, zip_path)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(Path.cwd() / "temp")
            
            # Move to java directory
            extracted_dir = Path.cwd() / "temp" / "jdk-21.0.4+7-jre"
            if extracted_dir.exists():
                if self.java_dir.exists():
                    import shutil
                    shutil.rmtree(self.java_dir)
                extracted_dir.rename(self.java_dir)
                
                # Cleanup
                zip_path.unlink()
                
                self.logger.info("Portable Java 21 installed successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to download portable Java: {e}")
            
        return False
