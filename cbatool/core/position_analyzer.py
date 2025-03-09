"""
Position analyzer module for CBAtool v2.0.

This module contains the PositionAnalyzer class responsible for analyzing
position data quality and detecting anomalies in cable position measurements.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

class PositionAnalyzer:
    """
    Class for analyzing cable position data quality and detecting position anomalies.
    
    Attributes:
        data (pd.DataFrame): The data to analyze.
        kp_column (str): Name of the column containing KP (kilometer point) values.
        dcc_column (str): Name of the column containing DCC (distance cross course) values.
        lat_column (str): Name of the column containing latitude values.
        lon_column (str): Name of the column containing longitude values.
        analysis_results (Dict): Dictionary containing results of various analyses.
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize the PositionAnalyzer with optional data.
        
        Args:
            data: DataFrame containing cable position data (optional).
        """
        self.data = data
        self.kp_column = None
        self.dcc_column = None
        self.lat_column = None
        self.lon_column = None
        self.analysis_results = {}
        
    def set_data(self, data: pd.DataFrame) -> bool:
        """
        Set the data to analyze.
        
        Args:
            data: DataFrame containing cable position data.
            
        Returns:
            bool: True if data was set successfully, False otherwise.
        """
        if data is None or data.empty:
            logger.error("Cannot set empty data for position analysis")
            return False
            
        self.data = data
        logger.info(f"Data set for position analysis: {len(data)} rows, {len(data.columns)} columns")
        return True
    
    def set_columns(self, kp_column: str, dcc_column: Optional[str] = None, 
                   lat_column: Optional[str] = None, lon_column: Optional[str] = None) -> bool:
        """
        Set the column names to use for position analysis.
        
        Args:
            kp_column: Name of the column containing KP values.
            dcc_column: Name of the column containing DCC values (optional).
            lat_column: Name of the column containing latitude values (optional).
            lon_column: Name of the column containing longitude values (optional).
            
        Returns:
            bool: True if columns were set successfully, False otherwise.
        """
        if self.data is None:
            logger.error("No data loaded for column setting")
            return False
            
        # Validate KP column exists
        if kp_column not in self.data.columns:
            logger.error(f"KP column '{kp_column}' not found in data")
            return False
            
        self.kp_column = kp_column
        logger.info(f"Using KP column: {kp_column}")
        
        # Set other columns if provided and valid
        if dcc_column and dcc_column in self.data.columns:
            self.dcc_column = dcc_column
            logger.info(f"Using DCC column: {dcc_column}")
        
        if lat_column and lat_column in self.data.columns:
            self.lat_column = lat_column
            logger.info(f"Using latitude column: {lat_column}")
        
        if lon_column and lon_column in self.data.columns:
            self.lon_column = lon_column
            logger.info(f"Using longitude column: {lon_column}")
                
        return True

    def analyze_position_data(self, kp_jump_threshold: float = 0.1, 
                            kp_reversal_threshold: float = 0.0001) -> bool:
        """
        Perform analysis on position data to detect anomalies and assess quality.
        
        Args:
            kp_jump_threshold: Threshold for detecting jumps in KP values.
            kp_reversal_threshold: Threshold for detecting reversals in KP values.
            
        Returns:
            bool: True if analysis was successful, False otherwise.
        """
        if self.data is None or self.kp_column is None:
            logger.error("Data or KP column not set for position analysis")
            return False
            
        logger.info("Starting position data analysis...")
        
        # Make a working copy of the data
        result = self.data.copy()
        
        # Analyze KP continuity
        result = self._analyze_kp_continuity(result, kp_jump_threshold, kp_reversal_threshold)
        
        # Analyze cross-track deviation if DCC column is available
        if self.dcc_column:
            result = self._analyze_cross_track_deviation(result)
        
        # Analyze coordinate consistency if lat/lon columns are available
        if self.lat_column and self.lon_column:
            result = self._analyze_coordinate_consistency(result)
        
        # Calculate overall position quality score
        result = self._calculate_position_quality(result)
        
        # Store results for later use
        self.data = result  # Update data with analysis results
        self.analysis_results['position_analysis'] = result
        
        # Calculate summary statistics
        self._calculate_summary_statistics()
        
        logger.info("Position analysis completed successfully")
        return True
    
    def _analyze_kp_continuity(self, data: pd.DataFrame, jump_threshold: float, 
                             reversal_threshold: float) -> pd.DataFrame:
        """
        Analyze continuity of KP (Kilometer Point) values.
        
        Args:
            data: DataFrame to analyze.
            jump_threshold: Threshold for detecting KP jumps.
            reversal_threshold: Threshold for detecting KP reversals.
            
        Returns:
            DataFrame with added KP continuity analysis columns.
        """
        logger.info("Analyzing KP continuity...")
        
        # Calculate KP differences between consecutive points
        data['KP_Diff'] = data[self.kp_column].diff()
        
        # Calculate median KP increment for reference
        median_kp_increment = data['KP_Diff'].median()
        logger.info(f"Median KP increment: {median_kp_increment:.6f}")
        
        # Detect KP jumps (large gaps)
        data['Is_KP_Jump'] = data['KP_Diff'] > (median_kp_increment + jump_threshold)
        
        # Detect KP reversals (negative progression)
        data['Is_KP_Reversal'] = data['KP_Diff'] < -reversal_threshold
        
        # Detect KP duplicates (zero progression)
        data['Is_KP_Duplicate'] = (data['KP_Diff'].abs() < reversal_threshold) & (~data['KP_Diff'].isna())
        
        # Count anomalies
        jump_count = data['Is_KP_Jump'].sum()
        reversal_count = data['Is_KP_Reversal'].sum()
        duplicate_count = data['Is_KP_Duplicate'].sum()
        
        logger.info(f"Found {jump_count} KP jumps, {reversal_count} KP reversals, and {duplicate_count} KP duplicates")
        
        # Calculate KP continuity score (1.0 = perfect, 0.0 = problematic)
        # Normalize KP difference by median increment
        normalized_diff = data['KP_Diff'] / median_kp_increment
        
        # Score based on deviation from expected increment
        data['KP_Continuity_Score'] = 1.0 / (1.0 + np.exp(5 * (abs(normalized_diff - 1.0) - 0.5)))
        
        # Override scores for special cases
        data.loc[data['Is_KP_Jump'], 'KP_Continuity_Score'] = 0.0
        data.loc[data['Is_KP_Reversal'], 'KP_Continuity_Score'] = 0.0
        data.loc[data['KP_Diff'].isna(), 'KP_Continuity_Score'] = 1.0  # First point
        
        return data
    
    def _analyze_cross_track_deviation(self, data: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
        """
        Analyze cross-track deviation (DCC).
        
        Args:
            data: DataFrame to analyze.
            threshold: Threshold for significant deviation (meters).
            
        Returns:
            DataFrame with added cross-track analysis columns.
        """
        if not self.dcc_column:
            return data
            
        logger.info("Analyzing cross-track deviation...")
        
        # Calculate absolute deviation
        data['DCC_Abs'] = data[self.dcc_column].abs()
        
        # Detect significant deviations
        data['Is_Significant_Deviation'] = data['DCC_Abs'] > threshold
        
        # Count significant deviations
        deviation_count = data['Is_Significant_Deviation'].sum()
        logger.info(f"Found {deviation_count} significant cross-track deviations (>{threshold}m)")
        
        # Calculate cross-track score using exponential decay
        data['Cross_Track_Score'] = np.exp(-(data['DCC_Abs'] / threshold))
        
        return data
    
    def _analyze_coordinate_consistency(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze consistency of coordinate progression.
        
        Args:
            data: DataFrame to analyze.
            
        Returns:
            DataFrame with added coordinate consistency analysis columns.
        """
        if not (self.lat_column and self.lon_column):
            return data
            
        logger.info("Analyzing coordinate consistency...")
        
        # Calculate distance between consecutive points (approx. using lat/lon differences)
        # For simplicity, we're using a rough approximation here
        data['Lat_Diff'] = data[self.lat_column].diff()
        data['Lon_Diff'] = data[self.lon_column].diff()
        
        # Simple Euclidean distance (not actual distance but useful for relative comparison)
        # In a real implementation, use the Haversine formula for actual distances
        data['Coord_Change'] = np.sqrt(data['Lat_Diff']**2 + data['Lon_Diff']**2)
        
        # Expected coordinate change based on KP difference
        # Rough approximation: 1 KP = 0.01 degrees (very approximate)
        data['Expected_Coord_Change'] = data['KP_Diff'] * 0.01
        
        # Detect coordinate inconsistencies
        data['Coord_Change_Ratio'] = np.where(
            data['Expected_Coord_Change'] > 0,
            data['Coord_Change'] / data['Expected_Coord_Change'],
            np.nan
        )
        
        # Score coordinate consistency (1.0 = perfect, 0.0 = problematic)
        data['Coord_Consistency_Score'] = np.exp(-abs(data['Coord_Change_Ratio'] - 1.0) * 2)
        
        # Fill NaNs with 1.0 (first point, etc.)
        data['Coord_Consistency_Score'] = data['Coord_Consistency_Score'].fillna(1.0)
        
        return data
    
    def _calculate_position_quality(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate overall position quality score.
        
        Args:
            data: DataFrame with individual quality scores.
            
        Returns:
            DataFrame with added overall position quality score.
        """
        logger.info("Calculating overall position quality score...")
        
        # Initialize position quality with KP continuity score
        data['Position_Quality_Score'] = data['KP_Continuity_Score']
        
        # If available, factor in cross-track score
        if 'Cross_Track_Score' in data.columns:
            data['Position_Quality_Score'] = data['Position_Quality_Score'] * 0.6 + data['Cross_Track_Score'] * 0.4
        
        # If available, factor in coordinate consistency score
        if 'Coord_Consistency_Score' in data.columns:
            data['Position_Quality_Score'] = data['Position_Quality_Score'] * 0.7 + data['Coord_Consistency_Score'] * 0.3
        
        # Categorize position quality
        data['Position_Quality'] = pd.cut(
            data['Position_Quality_Score'], 
            bins=[0, 0.3, 0.7, 1.0],
            labels=['Poor', 'Suspect', 'Good']
        )
        
        # Count by quality category
        quality_counts = data['Position_Quality'].value_counts().to_dict()
        for quality, count in quality_counts.items():
            logger.info(f"  {quality} quality: {count} points ({count/len(data)*100:.1f}%)")
        
        return data
    
    def _calculate_summary_statistics(self) -> None:
        """Calculate summary statistics for position analysis results."""
        if 'position_analysis' not in self.analysis_results:
            return
            
        data = self.analysis_results['position_analysis']
        
        # Create summary dictionary
        summary = {
            'total_points': len(data),
            'kp_range': (data[self.kp_column].min(), data[self.kp_column].max()),
            'kp_length': data[self.kp_column].max() - data[self.kp_column].min(),
            'quality_counts': data['Position_Quality'].value_counts().to_dict(),
            'anomalies': {
                'kp_jumps': data['Is_KP_Jump'].sum(),
                'kp_reversals': data['Is_KP_Reversal'].sum(),
                'kp_duplicates': data['Is_KP_Duplicate'].sum()
            }
        }
        
        # Add DCC statistics if available
        if self.dcc_column:
            summary['dcc_statistics'] = {
                'max_deviation': data[self.dcc_column].abs().max(),
                'mean_deviation': data[self.dcc_column].abs().mean(),
                'significant_deviations': data['Is_Significant_Deviation'].sum()
            }
        
        # Store summary
        self.analysis_results['summary'] = summary
        
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of position analysis results.
        
        Returns:
            Dictionary containing analysis summary.
        """
        if 'summary' not in self.analysis_results:
            return {'status': 'Position analysis not complete'}
            
        return self.analysis_results['summary']
    
    def identify_problem_segments(self, min_length: int = 5) -> pd.DataFrame:
        """
        Identify continuous segments with position quality issues.
        
        Args:
            min_length: Minimum number of consecutive points to consider as a segment.
            
        Returns:
            DataFrame with problem segments information.
        """
        if 'position_analysis' not in self.analysis_results:
            logger.error("Position analysis must be run before identifying problem segments")
            return pd.DataFrame()
            
        data = self.analysis_results['position_analysis']
        
        # Find segments with poor quality
        data['Is_Problem'] = data['Position_Quality'] == 'Poor'
        
        # Mark segment starts
        data['Segment_Start'] = (data['Is_Problem'] & ~data['Is_Problem'].shift(fill_value=False))
        
        # Assign segment IDs
        data['Segment_ID'] = data['Segment_Start'].cumsum()
        
        # Clear segment IDs for non-problem points
        data.loc[~data['Is_Problem'], 'Segment_ID'] = np.nan
        
        segments = []
        
        # Analyze each segment
        for segment_id, group in data[data['Is_Problem']].groupby('Segment_ID'):
            if len(group) < min_length:
                continue
                
            segment = {
                'Segment_ID': int(segment_id),
                'Start_KP': group[self.kp_column].min(),
                'End_KP': group[self.kp_column].max(),
                'Length_KP': group[self.kp_column].max() - group[self.kp_column].min(),
                'Point_Count': len(group),
                'Start_Index': group.index.min(),
                'End_Index': group.index.max(),
                'Avg_Quality_Score': group['Position_Quality_Score'].mean(),
                'Has_KP_Jumps': group['Is_KP_Jump'].any(),
                'Has_KP_Reversals': group['Is_KP_Reversal'].any()
            }
            
            # Add DCC information if available
            if self.dcc_column:
                segment['Max_DCC'] = group[self.dcc_column].abs().max()
                segment['Avg_DCC'] = group[self.dcc_column].abs().mean()
            
            segments.append(segment)
        
        # Create DataFrame from segments
        if segments:
            segments_df = pd.DataFrame(segments)
            segments_df = segments_df.sort_values('Start_KP')
            
            # Store in results
            self.analysis_results['problem_segments'] = segments_df
            
            logger.info(f"Identified {len(segments_df)} position problem segments")
            return segments_df
        else:
            logger.info("No position problem segments identified")
            self.analysis_results['problem_segments'] = pd.DataFrame()
            return pd.DataFrame()