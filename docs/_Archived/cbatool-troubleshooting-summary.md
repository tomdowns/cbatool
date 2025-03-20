# CBAtool v2.0 Troubleshooting Guide

This document summarizes the Python package structure issues encountered during the development of CBAtool v2.0 and the steps taken to resolve them.

## Common Import and Package Errors

### 1. Relative Import Beyond Top-Level Package

**Error Message:**
```
ImportError: attempted relative import beyond top-level package
```

**Cause:** Attempting to use relative imports (`from ..core import x`) when running a script directly rather than as part of a package.

**Solution:**
- Change `main-py.py` to `__main__.py` to follow Python package conventions
- Use relative imports (`.` for same directory, `..` for parent directory)
- Run the application as a module: `python -m cbatool` instead of running the script directly

**Example Fix:**
```python
# Change this:
from ui.app import CableAnalysisTool

# To this relative import:
from .ui.app import CableAnalysisTool
```

### 2. Circular Imports

**Error Message:**
```
ImportError: cannot import name 'file_operations' from partially initialized module 'cbatool.utils' (most likely due to a circular import)
```

**Cause:** Modules importing each other in a way that creates a dependency loop.

**Solution:**
- Simplify `__init__.py` files to avoid importing submodules
- Move imports inside functions where possible
- Use direct relative imports in affected modules

**Example Fix:**
```python
# Change this in __init__.py:
from . import file_operations

# To simply:
"""
Utility functions and helpers for CBAtool.
"""
# No imports
```

### 3. Missing/Misnamed Classes and Methods

**Error Message:**
```
ImportError: cannot import name 'Application' from 'cbatool.ui.app'
```

**Cause:** Trying to import a class or function that doesn't exist or has a different name.

**Solution:**
- Ensure consistency in class/function names across the project
- Update import statements to match the actual class names

**Example Fix:**
```python
# Change this:
from .app import Application

# To the actual class name:
from .app import CableAnalysisTool
```

### 4. Missing Method Implementation

**Error Message:**
```
AttributeError: 'Visualizer' object has no attribute '_add_anomaly_markers'
```

**Cause:** Methods referenced in code but not implemented, or empty method definitions.

**Solution:**
- Add the missing method implementations
- Fix empty method definitions (Python requires at least a `pass` statement)

**Example Methods Added:**
- `_add_anomaly_markers`: For adding anomaly markers to visualizations
- `_add_problem_section_highlighting`: For highlighting problem areas in visualizations
- `save_visualization`: For saving visualizations to HTML files
- `open_visualization`: For opening visualizations in a web browser

## Best Practices for Python Package Structure

### Package Organization

```
cbatool/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point (replaces main-py.py)
├── core/                # Core functionality
│   ├── __init__.py
│   ├── analyzer.py      # Data analysis
│   ├── data_loader.py   # Data loading
│   └── visualizer.py    # Visualization
├── ui/                  # User interface
│   ├── __init__.py
│   ├── app.py           # Main application interface
│   ├── dialogs.py       # Dialog boxes
│   └── widgets.py       # Custom widgets
└── utils/               # Utilities
    ├── __init__.py
    ├── constants.py     # Constants and configuration
    ├── error_handling.py # Error handling utilities
    └── file_operations.py # File operations
```

### Import Strategy

- **Relative imports** within the package:
  ```python
  from .module import Class  # Same directory
  from ..package import Module  # Parent directory
  ```

- **Absolute imports** for standard libraries:
  ```python
  import os
  import pandas as pd
  ```

### Running the Application

Run as a module (recommended):
```bash
python -m cbatool
```

This ensures Python treats the code as a package, making relative imports work correctly.

## Handling Missing Methods

When getting errors about missing methods, add the implementations as needed:

1. Check the error message to identify the missing method
2. Look at where it's being called to understand its purpose
3. Implement the method with the correct signature
4. Make sure the method is properly indented within the class

## Summary of Fixed Issues

1. Renamed `main-py.py` to `__main__.py` following Python conventions
2. Fixed relative import issues in multiple modules
3. Resolved circular imports by simplifying `__init__.py` files
4. Implemented missing methods in the `Visualizer` class:
   - `_add_anomaly_markers`
   - `_add_problem_section_highlighting`
   - `save_visualization`
   - `open_visualization`
5. Fixed method naming inconsistencies

These changes resulted in a properly structured Python package that can be run as a module, with clean import relationships and complete implementations of all required functionality.
