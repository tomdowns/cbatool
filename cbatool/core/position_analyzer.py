"""
Position analyzer module for CBAtool v2.0.

This module contains the PositionAnalyzer class responsible for analyzing
position data quality and detecting anomalies in cable position measurements.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple, Any, Union
from datetime import datetime

from .base_analyzer import BaseAnalyzer

# Configure logging
logger = logging.getLogger(__name__)

class PositionAnalyzer(BaseAnalyzer):
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
        super().__init__(data)
        self.dcc_column = None
        self.lat_column = None
        self.lon_column = None
        self.easting_column = None
        self.northing_column = None
        
    def _set_specific_columns(self, dcc_column: Optional[str] = None, 
                             lat_column: Optional[str] = None, 
                             lon_column: Optional[str] = None,
                             easting_column: Optional[str] = None, 
                             northing_column: Optional[str] = None,
                             **kwargs) -> bool:
        """
        Set position-specific column names for analysis.
        
        Args:
            dcc_column: Name of the column containing DCC values (optional).
            lat_column: Name of the column containing latitude values (optional).
            lon_column: Name of the column containing longitude values (optional).
            easting_column: Name of the column containing easting values (optional).
            northing_column: Name of the column containing northing values (optional).
            **kwargs: Additional column specifications not used by this analyzer.
            
        Returns:
            bool: True if columns were set successfully, False otherwise.
        """
        # Set DCC column if provided
        if dcc_column and dcc_column in self.data.columns:
            self.dcc_column = dcc_column
            logger.info(f"Using DCC column: {dcc_column}")
        else:
            self.dcc_column = None
            if dcc_column:  # Only log warning if a column was specified but not found
                logger.warning(f"DCC column '{dcc_column}' not found in data")
        
        # Set Lat/Lon columns
        if lat_column and lat_column in self.data.columns:
            self.lat_column = lat_column
            logger.info(f"Using latitude column: {lat_column}")
        else:
            self.lat_column = None
            if lat_column:  # Only log warning if a column was specified but not found
                logger.warning(f"Latitude column '{lat_column}' not found in data")
        
        if lon_column and lon_column in self.data.columns:
            self.lon_column = lon_column
            logger.info(f"Using longitude column: {lon_column}")
        else:
            self.lon_column = None
            if lon_column:  # Only log warning if a column was specified but not found
                logger.warning(f"Longitude column '{lon_column}' not found in data")
        
        # Set Easting/Northing columns
        if easting_column and easting_column in self.data.columns:
            self.easting_column = easting_column
            logger.info(f"Using easting column: {easting_column}")
        else:
            self.easting_column = None
            if easting_column:  # Only log warning if a column was specified but not found
                logger.warning(f"Easting column '{easting_column}' not found in data")
        
        if northing_column and northing_column in self.data.columns:
            self.northing_column = northing_column
            logger.info(f"Using northing column: {northing_column}")
        else:
            self.northing_column = None
            if northing_column:  # Only log warning if a column was specified but not found
                logger.warning(f"Northing column '{northing_column}' not found in data")
            
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
        return self.analyze_data(
            kp_jump_threshold=kp_jump_threshold, 
            kp_reversal_threshold=kp_reversal_threshold
        )
    
    def analyze_data(self, kp_jump_threshold: float = 0.1, 
                   kp_reversal_threshold: float = 0.0001, **kwargs) -> bool:
        """
        Perform analysis on position data to detect anomalies and assess quality.
        
        Args:
            kp_jump_threshold: Threshold for detecting jumps in KP values.
            kp_reversal_threshold: Threshold for detecting reversals in KP values.
            **kwargs: Additional parameters not used by this analyzer.
            
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
        
        # Analyze coordinate consistency if coordinate columns are available
        if self.lat_column and self.lon_column:
            result = self._analyze_coordinate_consistency(result)
        elif self.easting_column and self.northing_column:
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
        # Determine which coordinate system to use
        if self.easting_column and self.northing_column:
            logger.info("Analyzing coordinate consistency using Easting/Northing...")
            
            # Calculate distance using Easting/Northing (simpler than lat/lon)
            data['Easting_Diff'] = data[self.easting_column].diff()
            data['Northing_Diff'] = data[self.northing_column].diff()
            
            # Simple Euclidean distance
            data['Coord_Change'] = np.sqrt(data['Easting_Diff']**2 + data['Northing_Diff']**2)
            
            # Expected coordinate change based on KP difference (1 KP = 1000 meters)
            data['Expected_Coord_Change'] = data['KP_Diff'] * 1000
            
        elif self.lat_column and self.lon_column:
            logger.info("Analyzing coordinate consistency using Latitude/Longitude...")
            
            # Calculate using latitude/longitude
            data['Lat_Diff'] = data[self.lat_column].diff()
            data['Lon_Diff'] = data[self.lon_column].diff()
            
            # Simple Euclidean distance (not actual distance but useful for relative comparison)
            # In a real implementation, use the Haversine formula for actual distances
            data['Coord_Change'] = np.sqrt(data['Lat_Diff']**2 + data['Lon_Diff']**2)
            
            # Expected coordinate change based on KP difference
            # Rough approximation: 1 KP = 0.01 degrees (very approximate)
            data['Expected_Coord_Change'] = data['KP_Diff'] * 0.01
        else:
            logger.warning("No coordinate columns available for coordinate consistency analysis")
            # Initialize with empty values so subsequent code still works
            data['Coord_Change'] = 0
            data['Expected_Coord_Change'] = 0
        
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
        # First try to get standard summary from parent class
        summary = super().get_analysis_summary()
        
        # Add position-specific summary data
        if 'summary' in self.analysis_results:
            # Add key metrics from the detailed summary
            position_summary = self.analysis_results['summary']
            
            for key, value in position_summary.items():
                if key not in ['quality_counts', 'anomalies', 'dcc_statistics'] and not isinstance(value, dict):
                    summary[key] = value
                    
            # Add anomaly counts
            if 'anomalies' in position_summary:
                anomalies = position_summary['anomalies']
                summary['kp_jumps'] = anomalies.get('kp_jumps', 0)
                summary['kp_reversals'] = anomalies.get('kp_reversals', 0)
                summary['kp_duplicates'] = anomalies.get('kp_duplicates', 0)
            
            # Add quality distribution
            if 'quality_counts' in position_summary:
                quality_counts = position_summary['quality_counts']
                summary['quality_distribution'] = quality_counts
        
        return summary
    
    def identify_problem_sections(self, min_section_length: int = 5, **kwargs) -> pd.DataFrame:
        """
        Identify continuous sections with position quality issues.
        
        Args:
            min_section_length: Minimum number of consecutive points to consider as a segment.
            **kwargs: Additional parameters not used by this analyzer.
            
        Returns:
            DataFrame with problem sections information.
        """
        if 'position_analysis' not in self.analysis_results:
            logger.error("Position analysis must be run before identifying problem sections")
            return pd.DataFrame()
            
        data = self.analysis_results['position_analysis']
        
        # Find sections with poor quality
        data['Is_Problem'] = data['Position_Quality'] == 'Poor'
        
        # Mark segment starts
        data['Segment_Start'] = (data['Is_Problem'] & ~data['Is_Problem'].shift(fill_value=False))
        
        # Assign segment IDs
        data['Segment_ID'] = data['Segment_Start'].cumsum()
        
        # Clear segment IDs for non-problem points
        data.loc[~data['Is_Problem'], 'Segment_ID'] = np.nan
        
        sections = []
        
        # Analyze each segment
        for segment_id, group in data[data['Is_Problem']].groupby('Segment_ID'):
            if len(group) < min_section_length:
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
                'Has_KP_Reversals': group['Is_KP_Reversal'].any(),
                'Severity': self._determine_segment_severity(group)
            }
            
            # Add DCC information if available
            if self.dcc_column:
                segment['Max_DCC'] = group[self.dcc_column].abs().max()
                segment['Avg_DCC'] = group[self.dcc_column].abs().mean()
            
            sections.append(segment)
        
        # Create DataFrame from sections
        if sections:
            sections_df = pd.DataFrame(sections)
            sections_df = sections_df.sort_values('Start_KP')
            
            # Store in results
            self.analysis_results['problem_sections'] = sections_df
            
            logger.info(f"Identified {len(sections_df)} position problem sections")
            return sections_df
        else:
            logger.info("No position problem sections identified")
            self.analysis_results['problem_sections'] = pd.DataFrame()
            return pd.DataFrame()
            
    def _determine_segment_severity(self, segment_group: pd.DataFrame) -> str:
        """
        Determine severity of a problem segment based on quality score and anomalies.
        
        Args:
            segment_group: DataFrame containing the segment data
            
        Returns:
            str: Severity level ('High', 'Medium', or 'Low')
        """
        # Check for KP reversals (highest priority)
        if segment_group['Is_KP_Reversal'].any():
            return 'High'
            
        # Check for KP jumps
        if segment_group['Is_KP_Jump'].any():
            return 'Medium'
            
        # Check average quality score
        avg_quality = segment_group['Position_Quality_Score'].mean()
        
        if avg_quality < 0.2:
            return 'High'
        elif avg_quality < 0.5:
            return 'Medium'
        else:
            return 'Low'
            
    def _get_analysis_type(self) -> str:
        """Get the type of analysis."""
        return "position"
        
    def _populate_problem_sections(self, standardized: Dict[str, Any]) -> None:
        """
        Populate problem sections data in the standardized structure.
        
        Args:
            standardized: Dictionary with standardized structure to populate
        """
        if 'problem_sections' not in self.analysis_results or self.analysis_results['problem_sections'] is None or \
           isinstance(self.analysis_results['problem_sections'], pd.DataFrame) and self.analysis_results['problem_sections'].empty:
            return
            
        problem_sections = self.analysis_results['problem_sections']
        
        # Set total count
        standardized["problem_sections"]["total_count"] = len(problem_sections)
        
        # Populate severity breakdown
        if 'Severity' in problem_sections.columns:
            for severity in ['High', 'Medium', 'Low']:
                severity_key = severity.lower()
                sections = problem_sections[problem_sections['Severity'] == severity]
                count = len(sections)
                standardized["problem_sections"]["severity_breakdown"][severity_key]["count"] = count
                
                if 'Length_KP' in sections.columns:
                    # Convert KP length to meters (KP is in kilometers)
                    total_length = sections['Length_KP'].sum() * 1000
                    standardized["problem_sections"]["severity_breakdown"][severity_key]["total_length"] = total_length
        
        # Populate details
        for _, section in problem_sections.iterrows():
            # Extract key information
            detail = {
                "section_id": str(section.get('Segment_ID', '')),
                "severity": section.get('Severity', 'Medium').lower(),
                "start_position": section.get('Start_KP', 0.0),
                "end_position": section.get('End_KP', 0.0),
                "length": section.get('Length_KP', 0.0) * 1000,  # Convert KP to meters
                "deviation": 0.0,  # Position doesn't have a deviation concept like depth
                "recommended_action": self._get_position_recommendation(section)
            }
            standardized["problem_sections"]["details"].append(detail)
            
    def _get_position_recommendation(self, section: pd.Series) -> str:
        """
        Generate a recommendation for a position problem section.
        
        Args:
            section: Series containing section data
            
        Returns:
            str: Recommendation text
        """
        severity = section.get('Severity', 'Medium')
        
        if severity == 'High':
            if section.get('Has_KP_Reversals', False):
                return "Investigate KP reversals - potential data sequence issue"
            else:
                return "Review position data - critical quality issues detected"
        elif severity == 'Medium':
            if section.get('Has_KP_Jumps', False):
                return "Check for gaps in position data"
            else:
                return "Validate position measurements"
        else:
            return "Monitor position data quality"

    def _populate_anomalies(self, standardized: Dict[str, Any]) -> None:
        """
        Populate anomalies data in the standardized structure.
        
        Args:
            standardized: Dictionary with standardized structure to populate
        """
        # Get position analysis data
        if 'position_analysis' not in self.analysis_results or self.analysis_results['position_analysis'] is None:
            return
            
        position_data = self.analysis_results['position_analysis']
        
        # Find all anomalies (KP jumps, reversals, duplicates, significant deviations)
        anomaly_flags = ['Is_KP_Jump', 'Is_KP_Reversal', 'Is_KP_Duplicate', 'Is_Significant_Deviation']
        
        # Create mask for any anomaly
        anomaly_mask = False
        for flag in anomaly_flags:
            if flag in position_data.columns:
                anomaly_mask |= position_data[flag]
                
        # Filter anomalies
        anomalies = position_data[anomaly_mask]
        
        if anomalies.empty:
            return
            
        # Set total count
        standardized["anomalies"]["total_count"] = len(anomalies)
        
        # Populate severity breakdown
        high_count = len(anomalies[anomalies['Is_KP_Reversal']]) if 'Is_KP_Reversal' in anomalies.columns else 0
        medium_count = len(anomalies[anomalies['Is_KP_Jump']]) if 'Is_KP_Jump' in anomalies.columns else 0
        # Everything else is low
        low_count = len(anomalies) - high_count - medium_count
        
        standardized["anomalies"]["severity_breakdown"]["high"]["count"] = high_count
        standardized["anomalies"]["severity_breakdown"]["medium"]["count"] = medium_count 
        standardized["anomalies"]["severity_breakdown"]["low"]["count"] = low_count
        
        # Populate details
        for idx, anomaly in anomalies.iterrows():
            # Determine anomaly type and severity
            anomaly_type = "Unknown"
            severity = "low"
            
            if 'Is_KP_Reversal' in anomalies.columns and anomaly['Is_KP_Reversal']:
                anomaly_type = "KP Reversal"
                severity = "high"
            elif 'Is_KP_Jump' in anomalies.columns and anomaly['Is_KP_Jump']:
                anomaly_type = "KP Jump"
                severity = "medium"
            elif 'Is_KP_Duplicate' in anomalies.columns and anomaly['Is_KP_Duplicate']:
                anomaly_type = "KP Duplicate"
                severity = "low"
            elif 'Is_Significant_Deviation' in anomalies.columns and anomaly['Is_Significant_Deviation']:
                anomaly_type = "Significant Cross-Track Deviation"
                severity = "medium"
                
            # Extract key information and create standardized entry
            detail = {
                "anomaly_id": str(idx),
                "type": anomaly_type,
                "severity": severity,
                "position": anomaly.get(self.kp_column, 0.0),
                "deviation": anomaly.get('DCC_Abs', 0.0) if 'DCC_Abs' in anomaly else 0.0,
                "recommended_action": self._get_anomaly_recommendation(anomaly_type)
            }
            standardized["anomalies"]["details"].append(detail)
            
    def _get_anomaly_recommendation(self, anomaly_type: str) -> str:
        """
        Generate a recommendation for an anomaly.
        
        Args:
            anomaly_type: Type of anomaly
            
        Returns:
            str: Recommendation text
        """
        if anomaly_type == "KP Reversal":
            return "Investigate KP reversal - check data sequence"
        elif anomaly_type == "KP Jump":
            return "Validate cable length and check for missing data points"
        elif anomaly_type == "KP Duplicate":
            return "Check for duplicate measurements"
        elif anomaly_type == "Significant Cross-Track Deviation":
            return "Verify route alignment and validate survey data"
        else:
            return "Investigate position data anomaly"

    def _generate_recommendations(self, standardized: Dict[str, Any]) -> None:
        """
        Generate and add recommendations based on analysis results.
        
        Args:
            standardized: Dictionary with standardized structure to populate
        """
        # Add recommendations based on KP anomalies
        if 'summary' in self.analysis_results:
            summary = self.analysis_results['summary']
            if 'anomalies' in summary:
                anomalies = summary['anomalies']
                
                # KP reversals (high severity)
                kp_reversals = anomalies.get('kp_reversals', 0)
                if kp_reversals > 0:
                    standardized["recommendations"].append({
                        "category": "Position",
                        "severity": "High",
                        "description": f"Found {kp_reversals} KP reversals",
                        "action_items": ["Review data sequence and direction", 
                                       "Check for coordinate system issues"]
                    })
                
                # KP jumps (medium severity)
                kp_jumps = anomalies.get('kp_jumps', 0)
                if kp_jumps > 0:
                    standardized["recommendations"].append({
                        "category": "Position",
                        "severity": "Medium",
                        "description": f"Found {kp_jumps} KP jumps",
                        "action_items": ["Check for missing data points", 
                                       "Verify survey continuity"]
                    })
                
                # KP duplicates (low severity)
                kp_duplicates = anomalies.get('kp_duplicates', 0)
                if kp_duplicates > 0:
                    standardized["recommendations"].append({
                        "category": "Position",
                        "severity": "Low",
                        "description": f"Found {kp_duplicates} duplicate KP values",
                        "action_items": ["Review data for repeated measurements"]
                    })
        
        # Add recommendations based on position quality
        if 'position_analysis' in self.analysis_results:
            position_data = self.analysis_results['position_analysis']
            
            if 'Position_Quality' in position_data.columns:
                poor_count = (position_data['Position_Quality'] == 'Poor').sum()
                suspect_count = (position_data['Position_Quality'] == 'Suspect').sum()
                
                if poor_count > 0:
                    standardized["recommendations"].append({
                        "category": "Position Quality",
                        "severity": "Medium",
                        "description": f"Found {poor_count} points with poor position quality",
                        "action_items": ["Validate survey data", 
                                       "Check for equipment calibration issues"]
                    })
                
                if suspect_count > len(position_data) * 0.2:  # More than 20% suspect
                    standardized["recommendations"].append({
                        "category": "Position Quality",
                        "severity": "Low",
                        "description": f"High proportion of suspect quality positions ({suspect_count} points)",
                        "action_items": ["Consider recalibration of positioning equipment for future surveys"]
                    })
                    
        # Add recommendations based on cross-track deviation if available
        if self.dcc_column and 'position_analysis' in self.analysis_results:
            position_data = self.analysis_results['position_analysis']
            
            if 'Is_Significant_Deviation' in position_data.columns:
                deviation_count = position_data['Is_Significant_Deviation'].sum()
                
                if deviation_count > 0:
                    standardized["recommendations"].append({
                        "category": "Route Alignment",
                        "severity": "Medium",
                        "description": f"Found {deviation_count} points with significant cross-track deviation",
                        "action_items": ["Verify planned route alignment", 
                                       "Check for position reference inconsistencies"]
                    })
    
    def _populate_compliance_metrics(self, standardized: Dict[str, Any]) -> None:
        """
        Populate compliance metrics in the standardized structure.
        
        Args:
            standardized: Dictionary with standardized structure to populate
        """
        # For position analysis, compliance metrics are based on position quality
        if 'position_analysis' not in self.analysis_results:
            return
            
        position_data = self.analysis_results['position_analysis']
        
        # Calculate overall quality percentage (percentage of "Good" quality points)
        if 'Position_Quality' in position_data.columns:
            good_points = (position_data['Position_Quality'] == 'Good').sum()
            suspect_points = (position_data['Position_Quality'] == 'Suspect').sum()
            poor_points = (position_data['Position_Quality'] == 'Poor').sum()
            total_points = len(position_data)
            
            if total_points > 0:
                quality_percentage = (good_points / total_points) * 100
                standardized["compliance_metrics"]["total_compliance_percentage"] = quality_percentage
                
                # Also add quality distribution for reference
                standardized["compliance_metrics"]["quality_distribution"] = {
                    "good": good_points / total_points * 100,
                    "suspect": suspect_points / total_points * 100,
                    "poor": poor_points / total_points * 100
                }
        
        # Calculate compliance by severity if we have problem sections
        if 'problem_sections' in self.analysis_results and isinstance(self.analysis_results['problem_sections'], pd.DataFrame):
            problem_sections = self.analysis_results['problem_sections']
            
            if not problem_sections.empty and 'Severity' in problem_sections.columns and 'Length_KP' in problem_sections.columns:
                # Get total cable length from KP range
                if self.kp_column and self.kp_column in position_data.columns:
                    total_cable_length = (position_data[self.kp_column].max() - position_data[self.kp_column].min()) * 1000  # Convert to meters
                else:
                    total_cable_length = 1000  # Default value if KP info is not available
                    
                # Calculate percentages for each severity
                for severity in ['High', 'Medium', 'Low']:
                    severity_key = f"{severity.lower()}_risk_sections"
                    sections = problem_sections[problem_sections['Severity'] == severity]
                    
                    if not sections.empty:
                        total_length = sections['Length_KP'].sum() * 1000  # Convert KP to meters
                        percentage = (total_length / total_cable_length) * 100
                        standardized["compliance_metrics"]["compliance_by_severity"][severity_key] = percentage