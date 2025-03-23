"""
Core components for CBAtool including data loading, analysis, and visualization.
"""

# Lazy import to prevent circular imports
try:
    from .data_loader import DataLoader
    from .depth_analyzer import DepthAnalyzer
    from .position_analyzer import PositionAnalyzer
    from .visualizer import Visualizer
    
    __all__ = ['DataLoader', 'DepthAnalyzer', 'PositionAnalyzer', 'Visualizer']
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    __all__ = []