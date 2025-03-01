"""
File operation utilities for CBAtool v2.0.

This module contains utility functions for file operations,
such as selecting files and opening files with the default application.
"""

import os
import platform
import logging
from tkinter import Tk, filedialog

# Configure logging
logger = logging.getLogger(__name__)

# Detect operating system for platform-specific behavior
SYSTEM = platform.system()  # 'Darwin' for macOS, 'Windows' for Windows, 'Linux' for Linux


def select_file(initial_dir=None, title="Select Data File", file_types=None):
    """
    Open a file dialog to select a file, with platform-specific adjustments.
    
    Args:
        initial_dir: Initial directory to open the dialog in.
        title: Title for the file dialog.
        file_types: List of tuples with file type descriptions and patterns.
        
    Returns:
        The selected file path or empty string if canceled.
    """
    if initial_dir and not os.path.exists(initial_dir):
        initial_dir = os.path.expanduser("~")  # Default to home directory
        
    # Create a temporary root window
    root = Tk()
    root.withdraw()  # Hide the temporary window
    
    # Set default file types if not provided
    if file_types is None:
        file_types = [
            ("Excel Files", "*.xlsx *.xls"),
            ("CSV Files", "*.csv"),
            ("All Files", "*.*")
        ]
    
    # Configure file dialog based on platform
    if SYSTEM == "Darwin":  # macOS
        # macOS file dialogs work better with fewer restrictions
        file_path = filedialog.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=file_types
        )
    else:
        # Windows and Linux handle filetypes well
        file_path = filedialog.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=file_types
        )
    
    # Clean up temporary window
    root.destroy()
    
    return file_path


def open_file(file_path):
    """
    Open a file with the default application in a platform-independent way.
    
    Args:
        file_path: Path to the file to open.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
        
    try:
        if SYSTEM == 'Windows':
            os.startfile(file_path)
        elif SYSTEM == 'Darwin':  # macOS
            import subprocess
            subprocess.run(['open', file_path], check=True)
        else:  # Linux
            import subprocess
            subprocess.run(['xdg-open', file_path], check=True)
        
        logger.info(f"Opened file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to open file: {str(e)}")
        return False


def ensure_directory(directory_path):
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory_path: Path to the directory to create.
        
    Returns:
        bool: True if the directory exists or was created, False otherwise.
    """
    if not directory_path:
        return False
        
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            logger.info(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory: {str(e)}")
        return False


def get_file_info(file_path):
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        dict: Dictionary with file information.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
        
    try:
        file_info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'directory': os.path.dirname(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'size': os.path.getsize(file_path),
            'modified': os.path.getmtime(file_path),
        }
        
        return file_info
    except Exception as e:
        logger.error(f"Failed to get file info: {str(e)}")
        return None

def read_file(file_path, encoding='utf-8'):
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file.
        encoding: File encoding.
        
    Returns:
        str: File contents or None if an error occurred.
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file: {str(e)}")
        return None

def write_file(file_path, content, encoding='utf-8'):
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file.
        content: Content to write.
        encoding: File encoding.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write file: {str(e)}")
        return False