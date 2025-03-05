# AdvancedRangeSelector Documentation

## Overview

The `AdvancedRangeSelector` class is a sophisticated component of the CBAtool system designed to analyze cable burial data and identify meaningful segments for visualization. When dealing with large datasets (e.g., cables spanning 30+ kilometers), the ability to intelligently select relevant ranges becomes critical for effective data interpretation.

## Purpose

The primary purpose of the `AdvancedRangeSelector` is to:

1. Identify sections of interest in large cable burial datasets
2. Categorize and prioritize these sections based on their characteristics
3. Generate recommended viewing ranges that highlight important features
4. Provide properly formatted range information to visualization components

## Class Structure

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | The cable burial data to analyze |
| `depth_column` | `str` | Name of the column containing depth measurements |
| `position_column` | `str` | Name of the column containing position values (KP or index) |
| `target_depth` | `float` | Target burial depth for compliance checking (default: 1.5m) |
| `_ranges` | `List[Dict]` | Internal list of identified ranges |

### Primary Methods

| Method | Description |
|--------|-------------|
| `set_data(data)` | Set the DataFrame to analyze |
| `set_columns(depth_column, position_column)` | Set column names for analysis |
| `set_target_depth(target_depth)` | Set the target burial depth |
| `find_problem_sections(min_section_size, min_deficit)` | Identify sections with insufficient burial depth |
| `find_variation_zones(window_size, threshold_std)` | Identify zones with significant depth variations |
| `generate_recommended_ranges(max_ranges, min_range_size, max_range_size)` | Create recommended viewing ranges |
| `get_range_for_plotly(range_index)` | Get a specific range formatted for Plotly |
| `get_all_ranges_for_plotly()` | Get all ranges formatted for Plotly |

## Detailed Functionality

### Problem Section Detection

The class identifies areas where the cable burial depth falls below the specified target depth. The detection algorithm:

1. Identifies points where depth is below target (with a specified minimum deficit)
2. Groups continuous sections of non-compliant points
3. Calculates statistics for each section (size, min depth, max deficit)
4. Assigns an importance score based on deficit magnitude and section size

```python
# Example of problem section detection
range_selector.set_target_depth(1.5)  # Target depth in meters
problem_sections = range_selector.find_problem_sections(
    min_section_size=5,  # Minimum points to consider as a section
    min_deficit=0.1      # Minimum depth deficit in meters
)
```

#### Problem Section Attributes

Each identified problem section contains:

- `start_index`, `end_index`: Data indices for the section
- `start_position`, `end_position`: Position values (KP or index)
- `size`: Number of points in the section
- `min_depth`: Minimum depth in the section
- `max_deficit`: Maximum deficit below target depth
- `importance`: Calculated as `max_deficit * size`
- `type`: Always "deficit" for problem sections

### Variation Zone Detection

The class identifies areas with significant depth variations, which might indicate installation issues, seabed mobility, or other anomalies. The detection algorithm:

1. Calculates a rolling standard deviation of depth values using a specified window size
2. Identifies zones where standard deviation exceeds a threshold
3. Expands these zones to include appropriate context
4. Calculates statistics for each zone (std dev, depth range)
5. Assigns an importance score based on variation magnitude and zone size

```python
# Example of variation zone detection
variation_zones = range_selector.find_variation_zones(
    window_size=20,       # Size of rolling window
    threshold_std=0.2     # Standard deviation threshold
)
```

#### Variation Zone Attributes

Each identified variation zone contains:

- `start_index`, `end_index`: Data indices for the zone
- `start_position`, `end_position`: Position values (KP or index)
- `size`: Number of points in the zone
- `std_dev`: Standard deviation of depth in the zone
- `depth_range`: Range between minimum and maximum depth
- `importance`: Calculated as `std_dev * size`
- `type`: Always "variation" for variation zones

### Range Generation Algorithm

The intelligent range generation process:

1. Always includes a "Full Dataset" range covering the entire cable
2. Identifies the most severe depth deficit section and creates a range around it
3. Identifies the zone with highest depth variation and creates a range around it
4. Ensures ranges don't overlap significantly (using a configurable threshold)
5. Adds additional ranges based on section importance until the maximum number is reached

```python
# Example of range generation
recommended_ranges = range_selector.generate_recommended_ranges(
    max_ranges=5,        # Maximum number of ranges to recommend
    min_range_size=50,   # Minimum size of a range
    max_range_size=500   # Maximum size of a range
)
```

#### Range Attributes

Each generated range contains:

- `start_index`, `end_index`: Data indices for the range
- `start_position`, `end_position`: Position values (KP or index)
- `name`: Descriptive name (e.g., "Depth Deficit (0.7m)")
- `description`: Detailed description of the range
- `type`: "full", "deficit", or "variation"

### Plotly Integration

The class provides methods to format ranges specifically for Plotly visualizations:

```python
# Get a specific range formatted for Plotly
plotly_range = range_selector.get_range_for_plotly(1)  # Get the second range

# Get all ranges formatted for Plotly
all_plotly_ranges = range_selector.get_all_ranges_for_plotly()
```

The formatted ranges include:

- `x`: Array with start and end positions for the range selector
- `name`: Display name for the range
- `description`: Detailed description for tooltips or annotations

## Implementation Notes

### Importance Score Calculation

The importance score is a critical metric for prioritizing sections:

- For deficit sections: `importance = max_deficit * section_size`
  - This prioritizes sections with larger deficits that extend over longer distances
  - Example: A 50m section with a 0.7m deficit (importance = 35) is more critical than a 100m section with a 0.2m deficit (importance = 20)

- For variation zones: `importance = std_dev * section_size`
  - This prioritizes zones with higher variations that extend over longer distances
  - Example: A zone with std_dev of 0.5m over 60 points (importance = 30) is more significant than a zone with 0.3m std_dev over 70 points (importance = 21)

### Overlap Detection

To avoid recommending multiple ranges that cover essentially the same area, the class checks for significant overlap:

```python
def _ranges_overlap(self, range1, range2, overlap_threshold=0.5):
    """
    Check if two ranges overlap significantly.
    
    Args:
        range1: First range dictionary.
        range2: Second range dictionary.
        overlap_threshold: Threshold for considering overlap significant.
        
    Returns:
        bool: True if ranges overlap significantly.
    """
    # Calculate overlap
    start_max = max(range1['start_index'], range2['start_index'])
    end_min = min(range1['end_index'], range2['end_index'])
    
    if start_max <= end_min:  # There is overlap
        overlap = end_min - start_max + 1
        len1 = range1['end_index'] - range1['start_index'] + 1
        len2 = range2['end_index'] - range2['start_index'] + 1
        
        # Check if overlap is significant relative to either range
        return (overlap / len1 > overlap_threshold) or (overlap / len2 > overlap_threshold)
    
    return False
```

An overlap is considered significant if it covers more than a specified threshold (default 50%) of either range.

## Usage Examples

### Basic Usage

```python
# Create the range selector
range_selector = AdvancedRangeSelector()

# Set data and columns
range_selector.set_data(cable_data)
range_selector.set_columns(depth_column='DOB', position_column='KP')
range_selector.set_target_depth(1.5)  # 1.5m target depth

# Generate recommended ranges
ranges = range_selector.generate_recommended_ranges()

# Print the ranges
for i, range_info in enumerate(ranges):
    print(f"Range {i+1}: {range_info['name']}")
    print(f"  KP range: {range_info['start_position']:.3f} - {range_info['end_position']:.3f}")
    print(f"  Description: {range_info['description']}")
```

### Integration with Visualizer

```python
# Create the range selector and set data
range_selector = AdvancedRangeSelector()
range_selector.set_data(data)
range_selector.set_columns(depth_column='DOB', position_column='KP')

# Generate recommended ranges
ranges = range_selector.generate_recommended_ranges()

# Get Plotly-formatted range
plotly_range = range_selector.get_range_for_plotly(1)  # Get the second range

# Create a visualization with range selection
fig = create_visualization(data)

# Add range selector to the visualization
fig.update_layout(
    xaxis=dict(
        rangeslider=dict(visible=True),
        range=[plotly_range['x'][0], plotly_range['x'][1]]  # Set initial range
    )
)
```

## Performance Considerations

The `AdvancedRangeSelector` is designed to work efficiently with large datasets:

1. Uses vectorized Pandas operations instead of loops where possible
2. Employs rolling statistics for variation detection
3. Processes sections in order of importance to prioritize the most significant areas
4. Avoids re-analyzing data when generating multiple ranges

## Extensibility

The class is designed to be extensible for future development:

1. Additional section types can be added by creating new detection methods
2. The importance calculation can be customized for different use cases
3. Range generation can be modified to accommodate different prioritization schemes
4. The range formatting can be adapted for different visualization libraries
