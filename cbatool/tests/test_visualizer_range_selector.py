"""
Test script for the AdvancedRangeSelector integration with Visualizer.

This script tests the integration between the AdvancedRangeSelector and Visualizer classes.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add the parent directory to the Python path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the classes
from cbatool.core.visualizer import Visualizer
from cbatool.core.range_selector import AdvancedRangeSelector


def create_test_data(length=1000, target_depth=1.5):
    """Create synthetic cable burial data for testing."""
    
    # Create positions and KP values
    positions = np.arange(0, length)
    kp_values = positions / 1000.0  # Convert to kilometer points
    
    # Generate random depths with normal distribution
    np.random.seed(42)  # For reproducibility
    mean_depth = target_depth * 1.2  # Average is 20% more than target
    std_dev = target_depth * 0.15    # Standard deviation
    depths = np.random.normal(mean_depth, std_dev, length)
    
    # Create test problem sections
    # 1. Moderate deficit section (30cm below target)
    section1_start = int(length * 0.2)
    section1_end = int(length * 0.25)
    depths[section1_start:section1_end] = target_depth - 0.3
    
    # 2. Severe deficit section (70cm below target)
    section2_start = int(length * 0.6)
    section2_end = int(length * 0.63)
    depths[section2_start:section2_end] = target_depth - 0.7
    
    # 3. Minor deficit section (10cm below target)
    section3_start = int(length * 0.8)
    section3_end = int(length * 0.81)
    depths[section3_start:section3_end] = target_depth - 0.1
    
    # Create a high variation section
    section4_start = int(length * 0.4)
    section4_end = int(length * 0.45)
    for i in range(section4_start, section4_end, 5):
        # Create alternating depths to simulate high variation
        depths[i:i+2] = depths[i:i+2] + 0.5
        depths[i+2:i+4] = depths[i+2:i+4] - 0.5
    
    # Create the DataFrame
    test_data = pd.DataFrame({
        'Position': positions,
        'KP': kp_values,
        'Depth': depths  # Depth of Burial
    })
    
    return test_data


def test_visualizer_range_selector():
    """Test the integration of Visualizer with AdvancedRangeSelector."""
    
    print("Testing Visualizer with AdvancedRangeSelector integration...")
    
    # Create test data
    print("Creating test data...")
    data = create_test_data(length=1000, target_depth=1.5)
    print(f"Created test data with {len(data)} points")
    
    # Create and configure Visualizer
    visualizer = Visualizer()
    visualizer.set_data(data)
    visualizer.set_columns(depth_column='Depth', kp_column='KP')
    visualizer.set_target_depth(1.5)
    
    # Generate recommended ranges
    print("\nGenerating recommended ranges...")
    ranges = visualizer.generate_recommended_ranges()
    
    print(f"Generated {len(ranges)} recommended ranges:")
    for i, range_info in enumerate(ranges):
        print(f"  Range {i+1}: {range_info['name']}")
        print(f"    KP range: {range_info['start_position']:.3f} - {range_info['end_position']:.3f}")
        if 'description' in range_info:
            print(f"    Description: {range_info['description']}")
    
    # Create visualization with each range
    for i, range_info in enumerate(ranges):
        if i > 2:  # Limit to first 3 ranges to save time
            break
            
        print(f"\nCreating visualization with range {i+1}: {range_info['name']}...")
        fig = visualizer.create_visualization(initial_range_index=i)
        
        if fig:
            # Save the visualization to HTML for inspection
            output_file = f"range_{i+1}_{range_info['type']}.html"
            visualizer.save_visualization(output_file)
            print(f"  Saved visualization to {output_file}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_visualizer_range_selector()