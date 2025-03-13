"""
Deprecated: This module is maintained for backward compatibility.
Please use depth_analyzer module instead.
"""

import warnings
from .depth_analyzer import DepthAnalyzer

# Issue deprecation warning
warnings.warn(
    "The analyzer module is deprecated. Use depth_analyzer instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export DepthAnalyzer as Analyzer for backward compatibility
Analyzer = DepthAnalyzer