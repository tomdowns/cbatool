"""
User interface components for CBAtool application.
"""

# Import modules to make them accessible via cbatool.ui
from . import app
from . import widgets
from . import dialogs

# Expose any relevant classes (adjust as needed)
from .app import CableAnalysisTool
from .widgets import ScrollableFrame, ConsoleWidget
# Add any additional classes that should be exposed