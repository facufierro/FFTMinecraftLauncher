import os
import sys
import subprocess


def get_base_directory():
    """Get the directory where the executable or script is located"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)


def replace_file():
    """Replace FFTLauncher.exe with FFTLauncher.update"""
    base_dir = get_base_directory()
    exe_file = os.path.join(base_dir, "FFTLauncher.exe")
    update_file = os.path.join(base_dir, "FFTLauncher.update")
    
    try:
        # Check if update file exists
        if not os.path.exists(update_file):
            print("Error: FFTLauncher.update not found")
            return False
        
        # Remove the exe file if it exists
        if os.path.exists(exe_file):
            os.remove(exe_file)
            print("Removed FFTLauncher.exe")
        
        # Rename update file to exe
        os.rename(update_file, exe_file)
        print("Renamed FFTLauncher.update to FFTLauncher.exe")
        
        # Launch the new executable
        print("Launching FFTLauncher.exe...")
        subprocess.Popen([exe_file])
        
        return True
        
    except Exception as e:
        print(f"Error during file replacement: {e}")
        return False


def main():
    """Main entry point"""
    print("Starting file replacement...")
    
    if replace_file():
        print("File replacement completed successfully")
        print("FFTLauncher.exe has been launched")
    else:
        print("File replacement failed")
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
