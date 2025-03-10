"""
Configuration management utilities for CBAtool v2.0.

This module contains utilities for saving, loading, and managing configuration profiles
for the Cable Burial Analysis Tool.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Define default configuration structure
DEFAULT_CONFIG = {
    "configName": "Standard Cable Analysis",
    "description": "Default configuration for analyzing standard cables",
    "version": "1.0",
    "depthAnalysis": {
        "targetDepth": 1.5,
        "maxDepth": 3.0,
        "minDepth": 0.0,
        "spikeThreshold": 0.5,
        "windowSize": 5,
        "stdThreshold": 3.0,
        "ignoreAnomalies": False
    },
    "positionAnalysis": {
        "kpJumpThreshold": 0.1,
        "kpReversalThreshold": 0.0001,
        "dccThreshold": 5.0,
        "coordinateSystem": "WGS84"
    },
    "visualization": {
        "useSegmented": True,
        "includeAnomalies": True
    }
}

# Default configurations directory name
CONFIG_DIR = "configurations"


def get_config_directory() -> str:
    """
    Get the directory where configurations are stored.
    
    Returns:
        str: Path to the configuration directory.
    """
    # Use Documents folder for better user visibility
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, "Documents", "CBAtool", "Configurations")
    
    # Create directory if it doesn't exist
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
            logger.info(f"Created configuration directory: {config_dir}")
        except Exception as e:
            logger.error(f"Failed to create configuration directory: {str(e)}")
            # Fall back to current directory if Documents isn't accessible
            config_dir = "Configurations"
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
    
    return config_dir


def save_configuration(config: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Save a configuration to a JSON file.
    
    Args:
        config: Configuration dictionary to save.
        filename: Optional filename to save as.
        
    Returns:
        str: Path to the saved configuration file.
    """
    config_dir = get_config_directory()
    
    # If no filename provided, use the configuration name
    if not filename:
        # Replace spaces with underscores and remove special characters
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in config["configName"])
        filename = f"{safe_name}.json"
    
    # Ensure the filename has .json extension
    if not filename.lower().endswith('.json'):
        filename += '.json'
    
    file_path = os.path.join(config_dir, filename)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")
        raise


def load_configuration(filename: str) -> Dict[str, Any]:
    """
    Load a configuration from a JSON file.
    
    Args:
        filename: Path to the configuration file or just the filename.
        
    Returns:
        dict: Loaded configuration dictionary.
    """
    # If only a filename without path is provided, look in the config directory
    if os.path.dirname(filename) == "":
        config_dir = get_config_directory()
        file_path = os.path.join(config_dir, filename)
    else:
        file_path = filename
    
    # Ensure the filename has .json extension
    if not file_path.lower().endswith('.json'):
        file_path += '.json'
    
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {file_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        # Return default configuration if loading fails
        return DEFAULT_CONFIG.copy()


def get_available_configurations() -> List[Dict[str, str]]:
    """
    Get a list of available configuration files.
    
    Returns:
        list: List of dictionaries with information about each configuration file.
    """
    config_dir = get_config_directory()
    configurations = []
    
    try:
        if os.path.exists(config_dir):
            for filename in os.listdir(config_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(config_dir, filename)
                    try:
                        # Try to read the configuration name from the file
                        with open(file_path, 'r') as f:
                            config = json.load(f)
                            config_name = config.get("configName", os.path.splitext(filename)[0])
                            config_description = config.get("description", "")
                        
                        configurations.append({
                            "filename": filename,
                            "path": file_path,
                            "name": config_name,
                            "description": config_description
                        })
                    except:
                        # If we can't read the file, just use the filename
                        configurations.append({
                            "filename": filename,
                            "path": file_path,
                            "name": os.path.splitext(filename)[0],
                            "description": "Unable to read configuration details"
                        })
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
    
    return configurations


def validate_configuration(config: Dict[str, Any]) -> bool:
    """
    Validate a configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate.
        
    Returns:
        bool: True if configuration is valid, False otherwise.
    """
    # Check for required top-level keys
    required_keys = ["configName", "version", "depthAnalysis", "positionAnalysis", "visualization"]
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required key in configuration: {key}")
            return False
    
    # Check for required depth analysis keys
    depth_keys = ["targetDepth", "maxDepth", "spikeThreshold", "windowSize", "stdThreshold"]
    for key in depth_keys:
        if key not in config["depthAnalysis"]:
            logger.error(f"Missing required key in depthAnalysis: {key}")
            return False
    
    # Check for required position analysis keys
    position_keys = ["kpJumpThreshold", "kpReversalThreshold", "dccThreshold"]
    for key in position_keys:
        if key not in config["positionAnalysis"]:
            logger.error(f"Missing required key in positionAnalysis: {key}")
            return False
    
    # Check for required visualization keys
    viz_keys = ["useSegmented", "includeAnomalies"]
    for key in viz_keys:
        if key not in config["visualization"]:
            logger.error(f"Missing required key in visualization: {key}")
            return False
    
    return True


def create_default_configurations() -> None:
    """
    Create default configuration files if they don't already exist.
    """
    config_dir = get_config_directory()
    
    # Standard configuration (already defined as DEFAULT_CONFIG)
    standard_config = DEFAULT_CONFIG.copy()
    standard_path = os.path.join(config_dir, "Standard_Cable_Analysis.json")
    
    # High Sensitivity configuration
    high_sensitivity = DEFAULT_CONFIG.copy()
    high_sensitivity["configName"] = "High Sensitivity Analysis"
    high_sensitivity["description"] = "Configuration with lower thresholds for more sensitive analysis"
    high_sensitivity["depthAnalysis"]["spikeThreshold"] = 0.3
    high_sensitivity["depthAnalysis"]["stdThreshold"] = 2.0
    high_sensitivity["positionAnalysis"]["kpJumpThreshold"] = 0.05
    high_sensitivity["positionAnalysis"]["dccThreshold"] = 3.0
    high_sensitivity_path = os.path.join(config_dir, "High_Sensitivity_Analysis.json")
    
    # Deep Water configuration
    deep_water = DEFAULT_CONFIG.copy()
    deep_water["configName"] = "Deep Water Analysis"
    deep_water["description"] = "Configuration for analyzing deep water cable installations"
    deep_water["depthAnalysis"]["targetDepth"] = 2.0
    deep_water["depthAnalysis"]["maxDepth"] = 5.0
    deep_water_path = os.path.join(config_dir, "Deep_Water_Analysis.json")
    
    # Create the default configurations if they don't exist
    default_configs = [
        (standard_path, standard_config),
        (high_sensitivity_path, high_sensitivity),
        (deep_water_path, deep_water)
    ]
    
    for path, config in default_configs:
        if not os.path.exists(path):
            try:
                with open(path, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Created default configuration: {path}")
            except Exception as e:
                logger.error(f"Failed to create default configuration: {str(e)}")


# Create default configurations when module is imported
create_default_configurations()