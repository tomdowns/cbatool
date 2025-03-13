"""
CBAtool v2.0 - A comprehensive tool for data analysis and visualization.
"""
# Package metadata
__version__ = '2.0.0'
__author__ = 'Your Name'

# Import main classes to make them available at package level
try:
    from .core.data_loader import DataLoader
    from .core.depth_analyzer import DepthAnalyzer
    from .core.position_analyzer import PositionAnalyzer
    from .core.visualizer import Visualizer
except ImportError as e:
    print(f"Warning: Could not import main classes: {e}")