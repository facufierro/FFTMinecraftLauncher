"""Process management utilities for Windows operations."""

import subprocess
import time
import os
from typing import List, Optional
from .logging_utils import get_logger


class ProcessManager:
    """Utility class for managing Windows processes."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def is_process_running(self, process_name: str) -> bool:
        """Check if a process is currently running.
        
        Args:
            process_name: Name of the process (e.g., 'notepad.exe')
            
        Returns:
            True if process is running, False otherwise
        """
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                capture_output=True, text=True, timeout=5
            )
            
            return (process_name in result.stdout and 
                   'No tasks are running' not in result.stdout)
            
        except (subprocess.TimeoutExpired, Exception) as e:
            self.logger.debug(f"Error checking if {process_name} is running: {e}")
            return False
    
    def kill_process(self, process_name: str, force: bool = False) -> bool:
        """Kill a process by name.
        
        Args:
            process_name: Name of the process to kill
            force: If True, use /F flag for forceful termination
            
        Returns:
            True if process was killed or wasn't running, False if failed
        """
        try:
            if not self.is_process_running(process_name):
                self.logger.debug(f"Process {process_name} is not running")
                return True
            
            cmd = ['taskkill', '/IM', process_name, '/T']
            if force:
                cmd.append('/F')
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully killed process: {process_name}")
                return True
            else:
                self.logger.warning(f"Failed to kill {process_name}: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, Exception) as e:
            self.logger.error(f"Error killing process {process_name}: {e}")
            return False
    
    def kill_processes(self, process_names: List[str], force: bool = False, 
                      wait_between: float = 0.5) -> bool:
        """Kill multiple processes by name.
        
        Args:
            process_names: List of process names to kill
            force: If True, use forceful termination
            wait_between: Time to wait between each kill attempt
            
        Returns:
            True if all processes were killed, False if any failed
        """
        all_killed = True
        
        for process_name in process_names:
            if not self.kill_process(process_name, force):
                all_killed = False
            
            if wait_between > 0:
                time.sleep(wait_between)
        
        return all_killed
    
    def wait_for_process_exit(self, process_name: str, timeout: float = 10.0) -> bool:
        """Wait for a process to exit.
        
        Args:
            process_name: Name of the process to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if process exited, False if timeout reached
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.is_process_running(process_name):
                return True
            time.sleep(0.1)
        
        return False
    
    def close_process_gracefully(self, process_name: str, timeout: float = 5.0) -> bool:
        """Try to close a process gracefully, then force if necessary.
        
        Args:
            process_name: Name of the process to close
            timeout: Time to wait for graceful exit before forcing
            
        Returns:
            True if process was closed, False otherwise
        """
        if not self.is_process_running(process_name):
            return True
        
        # First try graceful termination
        if self.kill_process(process_name, force=False):
            # Wait for graceful exit
            if self.wait_for_process_exit(process_name, timeout):
                self.logger.info(f"Process {process_name} closed gracefully")
                return True
        
        # If graceful didn't work, force kill
        self.logger.warning(f"Forcing termination of {process_name}")
        return self.kill_process(process_name, force=True)
    
    def run_command(self, command: List[str], timeout: float = 30.0, 
                   capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command with consistent error handling.
        
        Args:
            command: Command to run as list of strings
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            CompletedProcess result
            
        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.SubprocessError: If command fails
        """
        try:
            self.logger.debug(f"Running command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0 and capture_output:
                self.logger.warning(f"Command failed with code {result.returncode}: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
            raise
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            raise


# Global process manager instance
_process_manager: Optional[ProcessManager] = None


def get_process_manager() -> ProcessManager:
    """Get the global process manager instance."""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager


# Convenience functions for common operations
def close_bootstrap_processes() -> bool:
    """Close any running bootstrap processes."""
    bootstrap_names = ['FFTMinecraftLauncher.exe', 'bootstrap.exe']
    return get_process_manager().kill_processes(bootstrap_names)


def is_bootstrap_running() -> bool:
    """Check if any bootstrap process is running."""
    bootstrap_names = ['FFTMinecraftLauncher.exe', 'bootstrap.exe']
    pm = get_process_manager()
    return any(pm.is_process_running(name) for name in bootstrap_names)
