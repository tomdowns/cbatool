import os
import sys

# Print current directory and Python path for debugging
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Try to locate the package files directly
core_path = os.path.join(os.getcwd(), 'cbatool', 'core')
print(f"Core path exists: {os.path.exists(core_path)}")
print(f"Files in core: {os.listdir(core_path) if os.path.exists(core_path) else 'N/A'}")

# Try importing modules individually
try:
    from cbatool.core import data_loader
    print("Successfully imported data_loader module")
    print(f"Contents: {dir(data_loader)}")
except ImportError as e:
    print(f"Failed to import data_loader module: {e}")

# Try importing classes directly  
try:
    from cbatool.core.data_loader import DataLoader
    print("Successfully imported DataLoader class")
except ImportError as e:
    print(f"Failed to import DataLoader class: {e}")