"""
Test script for the AdvancedRangeSelector class.

This script tests the core functionality of the AdvancedRangeSelector
by creating a sample dataset and testing each of its main methods.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add the parent directory to the Python path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AdvancedRangeSelector class
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


def test_problem_sections(range_selector, data):
    """Test the problem section detection."""
    
    # Set up the range selector
    range_selector.set_data(data)
    range_selector.set_columns(depth_column='Depth', position_column='KP')
    range_selector.set_target_depth(1.5)
    
    # Find problem sections
    problem_sections = range_selector.find_problem_sections()
    
    print(f"Found {len(problem_sections)} problem sections:")
    for i, section in enumerate(problem_sections):
        print(f"  Section {i+1}:")
        print(f"    KP range: {section['start_position']:.3f} - {section['end_position']:.3f}")
        print(f"    Min depth: {section['min_depth']:.2f}m")
        print(f"    Max deficit: {section['max_deficit']:.2f}m")
        print(f"    Importance score: {section['importance']:.2f}")
    
    return problem_sections


def test_variation_zones(range_selector, data):
    """Test the variation zone detection."""
    
    # Find variation zones
    variation_zones = range_selector.find_variation_zones()
    
    print(f"\nFound {len(variation_zones)} variation zones:")
    for i, zone in enumerate(variation_zones):
        print(f"  Zone {i+1}:")
        print(f"    KP range: {zone['start_position']:.3f} - {zone['end_position']:.3f}")
        print(f"    Std dev: {zone['std_dev']:.2f}m")
        print(f"    Depth range: {zone['depth_range']:.2f}m")
        print(f"    Importance score: {zone['importance']:.2f}")
    
    return variation_zones


def test_recommended_ranges(range_selector, data):
    """Test the recommended range generation."""
    
    # Generate recommended ranges with specific parameters
    recommended_ranges = range_selector.generate_recommended_ranges(
        max_ranges=5,
        min_range_size=40,  # Smaller minimum size to work with our test data
        max_range_size=200  # Smaller maximum size for our test dataset
    )
    
    print(f"\nGenerated {len(recommended_ranges)} recommended ranges:")
    for i, range_info in enumerate(recommended_ranges):
        print(f"  Range {i+1}: {range_info['name']}")
        print(f"    Index range: {range_info['start_index']} - {range_info['end_index']}")
        print(f"    KP range: {range_info['start_position']:.3f} - {range_info['end_position']:.3f}")
        print(f"    Description: {range_info['description']}")
        if 'type' in range_info:
            print(f"    Type: {range_info['type']}")
        print()
    
    return recommended_ranges


def visualize_test_results(data, problem_sections, variation_zones, recommended_ranges):
    """Create a simple visualization of the test results."""
    
    plt.figure(figsize=(12, 8))
    
    # Plot the depth data
    plt.plot(data['KP'], data['Depth'], 'b-', alpha=0.6, label='Depth')
    
    # Plot target depth
    plt.axhline(y=1.5, color='g', linestyle='--', label='Target Depth (1.5m)')
    
    # Highlight problem sections
    for section in problem_sections:
        plt.axvspan(
            section['start_position'], 
            section['end_position'], 
            alpha=0.3, 
            color='r',
            label='_Problem Section'  # Underscore prevents duplicate labels
        )
    
    # Highlight variation zones (only the top ones for clarity)
    if variation_zones:
        top_variations = sorted(variation_zones, key=lambda x: x['std_dev'], reverse=True)[:3]
        for zone in top_variations:
            plt.axvspan(
                zone['start_position'], 
                zone['end_position'], 
                alpha=0.2, 
                color='y',
                label='_Variation Zone'
            )
    
    # Add markers for the recommended ranges
    range_colors = ['m', 'c', 'g', 'orange', 'purple']
    for i, range_info in enumerate(recommended_ranges[1:]):  # Skip full dataset range
        if i >= len(range_colors):
            break
            
        start = range_info['start_position']
        end = range_info['end_position']
        
        # Add a colored bar below the main plot for each range
        y_pos = -0.2 - (i * 0.1)
        plt.plot(
            [start, end], 
            [y_pos, y_pos],
            color=range_colors[i],
            linewidth=4,
            label=f"Range: {range_info['name']}"
        )
        
        # Add vertical lines showing start/end of the range
        plt.axvline(x=start, color=range_colors[i], linestyle=':', alpha=0.7)
        plt.axvline(x=end, color=range_colors[i], linestyle=':', alpha=0.7)
    
    # Add labels and legend
    plt.xlabel('Cable Position (KP)')
    plt.ylabel('Depth (m)')
    plt.gca().invert_yaxis()  # Invert y-axis so deeper is lower
    plt.title('Range Selector Test Results')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    # Add text annotation for problem sections and variation zones
    plt.figtext(
        0.02, 0.02,
        f"Found {len(problem_sections)} problem sections and {len(variation_zones)} variation zones",
        ha='left'
    )
    
    # Show plot
    plt.tight_layout()
    plt.show()


def main():
    """Main test function."""
    
    print("Testing AdvancedRangeSelector...")
    
    # Create test data
    print("\nCreating test data...")
    test_data = create_test_data(length=1000, target_depth=1.5)
    print(f"Created test data with {len(test_data)} points")
    
    # Create the range selector
    range_selector = AdvancedRangeSelector()
    
    # Test problem section detection
    print("\nTesting problem section detection...")
    problem_sections = test_problem_sections(range_selector, test_data)
    
    # Test variation zone detection
    print("\nTesting variation zone detection...")
    variation_zones = test_variation_zones(range_selector, test_data)
    
    # Test recommended range generation
    print("\nTesting recommended range generation...")
    recommended_ranges = test_recommended_ranges(range_selector, test_data)
    
    # Test getting ranges for Plotly
    print("\nTesting Plotly range formatting...")
    plotly_ranges = range_selector.get_all_ranges_for_plotly()
    print(f"Generated {len(plotly_ranges)} formatted ranges for Plotly")
    
    # Visualize the results
    print("\nCreating visualization...")
    visualize_test_results(test_data, problem_sections, variation_zones, recommended_ranges)
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    main()