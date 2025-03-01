"""
Constants and configurations for CBAtool v2.0.

This module contains constants and default configurations used throughout the application.
"""

# Application information
APP_NAME = "Cable Burial Analysis Tool"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Thomas Downs"
APP_DATE = "March 2025"

# Default values
DEFAULT_TARGET_DEPTH = 1.5  # meters
DEFAULT_MAX_DEPTH = 3.0     # meters
DEFAULT_MIN_DEPTH = 0.0     # meters
DEFAULT_SPIKE_THRESHOLD = 0.5  # meters
DEFAULT_WINDOW_SIZE = 5      # data points
DEFAULT_STD_THRESHOLD = 3.0  # standard deviations

# File types
FILE_TYPES = [
    ("Excel Files", "*.xlsx *.xls"),
    ("CSV Files", "*.csv"),
    ("All Files", "*.*")
]

# Color schemes
COLORS = {
    "light": {
        "background": "#ffffff",
        "foreground": "#000000",
        "highlight": "#4a86e8",
        "console_bg": "#f0f0f0",
        "console_fg": "#000000",
        "error": "#ff0000",
        "warning": "#ffa500",
        "success": "#00aa00"
    },
    "dark": {
        "background": "#2d2d2d",
        "foreground": "#ffffff",
        "highlight": "#5c9ce6",
        "console_bg": "#1e1e1e",
        "console_fg": "#e0e0e0",
        "error": "#ff6b6b",
        "warning": "#ffc145",
        "success": "#5cdb5c"
    }
}

# Severity levels
SEVERITY_LEVELS = {
    "High": {
        "color": "red",
        "opacity": 0.3,
        "description": "Critical issue requiring immediate attention"
    },
    "Medium": {
        "color": "orange",
        "opacity": 0.2,
        "description": "Significant issue that should be addressed"
    },
    "Low": {
        "color": "yellow",
        "opacity": 0.15,
        "description": "Minor issue that may require monitoring"
    }
}

# Anomaly types
ANOMALY_TYPES = {
    "Exceeds maximum trenching depth": {
        "severity": "High",
        "marker": "x",
        "color": "red",
        "description": "Depth value exceeds maximum physically possible trenching depth"
    },
    "Invalid depth (below minimum)": {
        "severity": "High",
        "marker": "x",
        "color": "red",
        "description": "Depth value is below minimum valid depth (typically 0)"
    },
    "Sudden depth change": {
        "severity": "Medium",
        "marker": "triangle-up",
        "color": "orange",
        "description": "Abrupt change in depth between adjacent measurements"
    },
    "Statistical outlier": {
        "severity": "Medium",
        "marker": "circle",
        "color": "gold",
        "description": "Value deviates significantly from local trend"
    },
    "Unknown anomaly": {
        "severity": "Low",
        "marker": "circle",
        "color": "gray",
        "description": "Other unspecified anomaly type"
    }
}

# Output file names
OUTPUT_FILES = {
    "visualization": "cable_burial_analysis.html",
    "problem_sections": "problem_sections_report.xlsx",
    "anomalies": "anomaly_report.xlsx",
    "summary": "analysis_summary.xlsx"
}
