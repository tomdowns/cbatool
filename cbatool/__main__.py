"""
Main entry point for CBAtool v2.0.

This file serves as the entry point for the Cable Burial Analysis Tool, launching
the graphical user interface and initializing the application.
"""

import os
import sys
import logging
import platform
import sv_ttk
from typing import Optional
import traceback

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Check platform
SYSTEM = platform.system()  # 'Darwin' for macOS, 'Windows' for Windows, 'Linux' for Linux


def ensure_dependencies() -> bool:
    """
    Check if required libraries are installed and guide the user if they're not.
    
    Returns:
        bool: True if all dependencies are available, False otherwise.
    """
    try:
        # Check required libraries
        import pandas
        import numpy
        import plotly
        return True
    except ImportError as e:
        missing_lib = str(e).split("'")[1]
        error_msg = (
            f"Required library '{missing_lib}' is not installed.\n\n"
            f"Please install the required packages by running:\n"
            f"pip install pandas numpy plotly"
        )
        print(error_msg)
        return False


def main() -> None:
    """
    Main entry point for the application.
    Initializes the UI and starts the application.
    """
    # Check dependencies
    if not ensure_dependencies():
        sys.exit(1)
    
    try:
        # Import modules after dependency check
        from .ui.app import CableAnalysisTool
        
        # Initialize tkinter
        from tkinter import Tk
        
        # Create application window
       
        root = Tk()
        sv_ttk.set_theme("dark")
        app = CableAnalysisTool(root)
        
        # Start main event loop
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
