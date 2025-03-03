"""
Range selector module for CBAtool v2.0.

This module contains the AdvancedRangeSelector class responsible for identifying
meaningful data ranges for visualization, especially for large datasets.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

class AdvancedRangeSelector:
    """
    Class for intelligently selecting optimal data ranges for visualization.
    
    This class analyzes cable burial data to identify sections of interest,
    such as areas with depth deficits or significant depth variations,
    and recommends appropriate viewing ranges.
    
    Attributes:
        data (pd.DataFrame): The data to analyze.
        depth_column (str): Name of the column containing depth measurements.
        position_column (str): Name of the column containing position values (could be KP or index).
        target_depth (float): Target burial depth for compliance checking.
        _ranges (List[Dict]): List of identified ranges.
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None, 
                 depth_column: Optional[str] = None,
                 position_column: Optional[str] = None,
                 target_depth: float = 1.5):
        """
        Initialize the AdvancedRangeSelector with optional data.
        
        Args:
            data: DataFrame containing cable burial data (optional).
            depth_column: Name of the column containing depth measurements.
            position_column: Name of the column containing position values.
            target_depth: Target burial depth in meters.
        """
        self.data = data
        self.depth_column = depth_column
        self.position_column = position_column
        self.target_depth = target_depth
        self._ranges = []
        
    def set_data(self, data: pd.DataFrame) -> bool:
        """
        Set the data to analyze.
        
        Args:
            data: DataFrame containing cable burial data.
            
        Returns:
            bool: True if data was set successfully, False otherwise.
        """
        if data is None or data.empty:
            logger.error("Cannot set empty data for range selection")
            return False
            
        self.data = data
        logger.info(f"Data set for range selection: {len(data)} rows")
        return True
    
    def set_columns(self, depth_column: str, position_column: Optional[str] = None) -> bool:
        """
        Set the column names to use for analysis.
        
        Args:
            depth_column: Name of the column containing depth measurements.
            position_column: Name of the column containing position values (optional).
            
        Returns:
            bool: True if columns were set successfully, False otherwise.
        """
        if self.data is None:
            logger.error("No data loaded for column setting")
            return False
            
        # Validate depth column exists
        if depth_column not in self.data.columns:
            logger.error(f"Depth column '{depth_column}' not found in data")
            return False
            
        self.depth_column = depth_column
        
        # Validate position column if provided
        if position_column:
            if position_column not in self.data.columns:
                logger.warning(f"Position column '{position_column}' not found, using index instead")
                self.position_column = None
            else:
                self.position_column = position_column
                logger.info(f"Using position column: {position_column}")
        else:
            self.position_column = None
            logger.info("No position column specified, using index")
            
        return True
    
    def set_target_depth(self, target_depth: float) -> None:
        """
        Set the target burial depth for compliance checking.
        
        Args:
            target_depth: Target depth in meters.
        """
        self.target_depth = target_depth
        logger.info(f"Target depth set to {target_depth}m")
    
    def find_problem_sections(self, min_section_size: int = 5, 
                            min_deficit: float = 0.1) -> List[Dict]:
        """
        Find sections where the cable depth is below target depth.
        
        Args:
            min_section_size: Minimum number of points to consider as a section.
            min_deficit: Minimum depth deficit in meters to consider.
            
        Returns:
            List of dictionaries describing problem sections.
        """
        if self.data is None or self.depth_column is None:
            logger.error("Data or depth column not set for finding problem sections")
            return []
        
        # Get position values (use index if no position column)
        if self.position_column:
            positions = self.data[self.position_column]
        else:
            positions = self.data.index.astype(float)
        
        # Identify points below target depth
        below_target = self.data[self.depth_column] < (self.target_depth - min_deficit)
        
        # Find continuous sections
        section_starts = below_target & (~below_target.shift(1, fill_value=False))
        section_ends = below_target & (~below_target.shift(-1, fill_value=False))
        
        start_indices = list(section_starts[section_starts].index)
        end_indices = list(section_ends[section_ends].index)
        
        problem_sections = []
        
        for start_idx, end_idx in zip(start_indices, end_indices):
            section_size = end_idx - start_idx + 1
            
            if section_size >= min_section_size:
                # Calculate section statistics
                section_data = self.data.loc[start_idx:end_idx]
                min_depth = section_data[self.depth_column].min()
                max_deficit = self.target_depth - min_depth
                
                # Get position range
                start_pos = positions[start_idx]
                end_pos = positions[end_idx]
                
                # Create section info
                section = {
                    'start_index': start_idx,
                    'end_index': end_idx,
                    'start_position': start_pos,
                    'end_position': end_pos,
                    'size': section_size,
                    'min_depth': min_depth,
                    'max_deficit': max_deficit,
                    'importance': max_deficit * section_size,  # Importance score
                    'type': 'deficit'
                }
                
                problem_sections.append(section)
        
        logger.info(f"Found {len(problem_sections)} problem sections with depth deficit > {min_deficit}m")
        return problem_sections
    
    def find_variation_zones(self, window_size: int = 20, 
                           threshold_std: float = 0.2) -> List[Dict]:
        """
        Find zones with significant depth variations.
        
        Args:
            window_size: Size of rolling window for standard deviation calculation.
            threshold_std: Threshold standard deviation to consider as significant.
            
        Returns:
            List of dictionaries describing variation zones.
        """
        if self.data is None or self.depth_column is None:
            logger.error("Data or depth column not set for finding variation zones")
            return []
        
        # Calculate rolling standard deviation
        rolling_std = self.data[self.depth_column].rolling(window=window_size, center=True).std()
        
        # Get position values (use index if no position column)
        if self.position_column:
            positions = self.data[self.position_column]
        else:
            positions = self.data.index.astype(float)
        
        # Identify high variation zones
        high_var = rolling_std > threshold_std
        
        # Find continuous sections
        section_starts = high_var & (~high_var.shift(1, fill_value=False))
        section_ends = high_var & (~high_var.shift(-1, fill_value=False))
        
        start_indices = list(section_starts[section_starts].index)
        end_indices = list(section_ends[section_ends].index)
        
        variation_zones = []
        
        for start_idx, end_idx in zip(start_indices, end_indices):
            # Expand window to include full rolling window context
            start_context = max(0, start_idx - window_size // 2)
            end_context = min(len(self.data) - 1, end_idx + window_size // 2)
            
            # Calculate zone statistics
            zone_data = self.data.loc[start_context:end_context]
            section_size = end_context - start_context + 1
            
            if section_size >= window_size // 2:  # Ensure zone is meaningful
                zone_std = zone_data[self.depth_column].std()
                zone_range = zone_data[self.depth_column].max() - zone_data[self.depth_column].min()
                
                # Get position range
                start_pos = positions[start_context]
                end_pos = positions[end_context]
                
                # Create zone info
                zone = {
                    'start_index': start_context,
                    'end_index': end_context,
                    'start_position': start_pos,
                    'end_position': end_pos,
                    'size': section_size,
                    'std_dev': zone_std,
                    'depth_range': zone_range,
                    'importance': zone_std * section_size,  # Importance score
                    'type': 'variation'
                }
                
                variation_zones.append(zone)
        
        logger.info(f"Found {len(variation_zones)} zones with significant depth variations (std > {threshold_std})")
        return variation_zones
    
    def generate_recommended_ranges(self, max_ranges: int = 5, 
                                 min_range_size: int = 50,
                                 max_range_size: int = 500) -> List[Dict]:
        """
        Generate recommended viewing ranges based on problem sections and variation zones.
        
        Args:
            max_ranges: Maximum number of ranges to recommend.
            min_range_size: Minimum size of a recommended range.
            max_range_size: Maximum size of a recommended range.
            
        Returns:
            List of dictionaries with recommended viewing ranges.
        """
        if self.data is None or self.depth_column is None:
            logger.error("Data or depth column not set for generating ranges")
            return []
        
        # Find problem sections and variation zones
        # Use explicit parameters to ensure we detect sections
        problem_sections = self.find_problem_sections(min_section_size=3, min_deficit=0.1)
        variation_zones = self.find_variation_zones(window_size=20, threshold_std=0.3)
        
        logger.info(f"Found {len(problem_sections)} problem sections and {len(variation_zones)} variation zones for range generation")
        
        # Get position values (use index if no position column)
        if self.position_column:
            positions = self.data[self.position_column].values  # Convert to numpy array for consistent access
        else:
            positions = np.array(self.data.index)
        
        recommended_ranges = []
        
        # Add one range for the entire dataset
        full_range = {
            'start_index': 0,
            'end_index': len(self.data) - 1,
            'start_position': positions[0],
            'end_position': positions[-1],
            'name': 'Full Dataset',
            'description': f'Complete view of all {len(self.data)} data points',
            'type': 'full'
        }
        recommended_ranges.append(full_range)
        
        # Directly add ranges for the top problem sections
        if problem_sections:
            # Get the most severe deficit section
            top_deficit = max(problem_sections, key=lambda x: x['max_deficit'])
            
            # Calculate expanded context
            context_size = min(100, len(self.data) // 10)  # 10% of data or 100 points, whichever is smaller
            mid_index = (top_deficit['start_index'] + top_deficit['end_index']) // 2
            
            start_idx = max(0, mid_index - context_size // 2)
            end_idx = min(len(self.data) - 1, mid_index + context_size // 2)
            
            deficit_range = {
                'start_index': start_idx,
                'end_index': end_idx,
                'start_position': positions[start_idx],
                'end_position': positions[end_idx],
                'name': f"Depth Deficit ({top_deficit['max_deficit']:.2f}m)",
                'description': f"Section with burial depth {top_deficit['max_deficit']:.2f}m below target",
                'type': 'deficit'
            }
            recommended_ranges.append(deficit_range)
            logger.info(f"Added range for depth deficit: {deficit_range['start_position']:.3f}-{deficit_range['end_position']:.3f}")
        
        # Add range for the top variation zone (if any)
        if variation_zones:
            # Get the zone with highest variation
            top_variation = max(variation_zones, key=lambda x: x['std_dev'])
            
            # Calculate expanded context (make sure the context size is reasonable)
            context_size = min(100, len(self.data) // 10)  # 10% of data or 100 points, whichever is smaller
            mid_index = (top_variation['start_index'] + top_variation['end_index']) // 2
            
            start_idx = max(0, mid_index - context_size // 2)
            end_idx = min(len(self.data) - 1, mid_index + context_size // 2)
            
            variation_range = {
                'start_index': start_idx,
                'end_index': end_idx,
                'start_position': positions[start_idx],
                'end_position': positions[end_idx],
                'name': f"Depth Variation (±{top_variation['depth_range']:.2f}m)",
                'description': f"Section with significant depth variations (std: {top_variation['std_dev']:.2f}m)",
                'type': 'variation'
            }
            
            # Only add if it doesn't overlap significantly with the deficit range
            overlap = False
            for existing_range in recommended_ranges[1:]:  # Skip the full dataset range
                if self._ranges_overlap(variation_range, existing_range, 0.7):
                    overlap = True
                    logger.info(f"Skipping variation range due to overlap with existing range")
                    break
                    
            if not overlap:
                recommended_ranges.append(variation_range)
                logger.info(f"Added range for depth variation: {variation_range['start_position']:.3f}-{variation_range['end_position']:.3f}")
            elif len(variation_zones) > 1:
                # Try the second highest variation if available and not overlapping
                second_variation = variation_zones[1]
                mid_index = (second_variation['start_index'] + second_variation['end_index']) // 2
                
                start_idx = max(0, mid_index - context_size // 2)
                end_idx = min(len(self.data) - 1, mid_index + context_size // 2)
                
                second_var_range = {
                    'start_index': start_idx,
                    'end_index': end_idx,
                    'start_position': positions[start_idx],
                    'end_position': positions[end_idx],
                    'name': f"Depth Variation (±{second_variation['depth_range']:.2f}m)",
                    'description': f"Section with significant depth variations (std: {second_variation['std_dev']:.2f}m)",
                    'type': 'variation'
                }
                
                # Check again for overlap
                if not any(self._ranges_overlap(second_var_range, r, 0.7) for r in recommended_ranges[1:]):
                    recommended_ranges.append(second_var_range)
                    logger.info(f"Added alternative range for depth variation: {second_var_range['start_position']:.3f}-{second_var_range['end_position']:.3f}")
        
        # Fill remaining slots with combined approach if we didn't get enough ranges
        if len(recommended_ranges) < max_ranges and (problem_sections or variation_zones):
            # Combine and sort all sections by importance
            all_sections = problem_sections + variation_zones
            all_sections.sort(key=lambda x: x['importance'], reverse=True)
            
            # Skip sections already covered in our top picks
            for section in all_sections:
                if len(recommended_ranges) >= max_ranges:
                    break
                    
                # Calculate expanded context
                context_size = min(100, len(self.data) // 10)
                mid_index = (section['start_index'] + section['end_index']) // 2
                
                start_idx = max(0, mid_index - context_size // 2)
                end_idx = min(len(self.data) - 1, mid_index + context_size // 2)
                
                if section['type'] == 'deficit':
                    name = f"Depth Deficit ({section['max_deficit']:.2f}m)"
                    description = f"Section with burial depth {section['max_deficit']:.2f}m below target"
                else:
                    name = f"Depth Variation (±{section['depth_range']:.2f}m)"
                    description = f"Section with significant depth variations (std: {section['std_dev']:.2f}m)"
                
                range_info = {
                    'start_index': start_idx,
                    'end_index': end_idx,
                    'start_position': positions[start_idx],
                    'end_position': positions[end_idx],
                    'name': name,
                    'description': description,
                    'type': section['type']
                }
                
                # Check if this range overlaps with any existing range
                if not any(self._ranges_overlap(range_info, r, 0.5) for r in recommended_ranges):
                    recommended_ranges.append(range_info)
                    logger.info(f"Added additional range: {range_info['name']}")
        
        self._ranges = recommended_ranges
        logger.info(f"Generated {len(recommended_ranges)} recommended viewing ranges")
        return recommended_ranges
    
    def _ranges_overlap(self, range1: Dict, range2: Dict, overlap_threshold: float = 0.5) -> bool:
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
    
    def get_range_for_plotly(self, range_index: int = 0) -> Dict:
        """
        Get range information formatted for Plotly range selector.
        
        Args:
            range_index: Index of the range to get (from the recommended ranges).
            
        Returns:
            Dictionary with range information formatted for Plotly.
        """
        if not self._ranges or range_index >= len(self._ranges):
            logger.warning("No ranges available or invalid range index")
            return {}
        
        selected_range = self._ranges[range_index]
        
        # Format for Plotly (depends on what we're using for x-axis)
        if self.position_column:
            plotly_range = {
                'x': [selected_range['start_position'], selected_range['end_position']],
                'name': selected_range['name'],
                'description': selected_range['description']
            }
        else:
            plotly_range = {
                'x': [selected_range['start_index'], selected_range['end_index']],
                'name': selected_range['name'],
                'description': selected_range['description']
            }
        
        return plotly_range
    
    def get_all_ranges_for_plotly(self) -> List[Dict]:
        """
        Get all recommended ranges formatted for Plotly.
        
        Returns:
            List of dictionaries with range information formatted for Plotly.
        """
        return [self.get_range_for_plotly(i) for i in range(len(self._ranges))]