"""
Analyzer module for CBAtool v2.0.

This module contains the Analyzer class responsible for performing various
analyses on cable burial data, including anomaly detection and compliance checking.
The Analyzer class breaks down the analysis process into smaller, more focused
methods for better maintainability and clarity.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

class Analyzer:
    """
    Class for analyzing cable burial data, detecting anomalies, and checking compliance.
    
    Attributes:
        data (pd.DataFrame): The data to analyze.
        depth_column (str): Name of the column containing depth measurements.
        kp_column (str): Name of the column containing KP (kilometer point) values.
        position_column (str): Name of the column containing position values.
        target_depth (float): Target burial depth for compliance checking.
        analysis_results (Dict): Dictionary containing results of various analyses.
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize the Analyzer with optional data.
        
        Args:
            data: DataFrame containing cable burial data (optional).
        """
        self.data = data
        self.depth_column = None
        self.kp_column = None
        self.position_column = None
        self.target_depth = 1.5  # Default target depth in meters
        self.analysis_results = {}
        
    def set_data(self, data: pd.DataFrame) -> bool:
        """
        Set the data to analyze.
        
        Args:
            data: DataFrame containing cable burial data.
            
        Returns:
            bool: True if data was set successfully, False otherwise.
        """
        if data is None or data.empty:
            logger.error("Cannot set empty data for analysis")
            return False
            
        self.data = data
        logger.info(f"Data set for analysis: {len(data)} rows, {len(data.columns)} columns")
        return True
    
    def set_columns(self, depth_column: str, kp_column: Optional[str] = None, 
                  position_column: Optional[str] = None) -> bool:
        """
        Set the column names to use for analysis.
        
        Args:
            depth_column: Name of the column containing depth measurements.
            kp_column: Name of the column containing KP values (optional).
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
        logger.info(f"Using depth column: {depth_column}")
        
        # Validate KP column if provided
        if kp_column and kp_column in self.data.columns:
            self.kp_column = kp_column
            logger.info(f"Using KP column: {kp_column}")
        else:
            self.kp_column = None
            if kp_column:  # Only log error if a column was specified but not found
                logger.warning(f"KP column '{kp_column}' not found in data")
        
        # Validate position column if provided
        if position_column and position_column in self.data.columns:
            self.position_column = position_column
            logger.info(f"Using position column: {position_column}")
        else:
            self.position_column = None
            if position_column:  # Only log error if a column was specified but not found
                logger.warning(f"Position column '{position_column}' not found in data")
                
        return True
    
    def set_target_depth(self, target_depth: float) -> None:
        """
        Set the target burial depth for compliance checking.
        
        Args:
            target_depth: Target depth in meters.
        """
        self.target_depth = target_depth
        logger.info(f"Target depth set to {target_depth}m")
    
    def analyze_data(self, max_depth: float = 3.0, min_depth: float = 0.0,
                  spike_threshold: float = 0.5, window_size: int = 5,
                  std_threshold: float = 3.0, ignore_anomalies: bool = False) -> bool:
        """
        Perform full analysis on the data, including anomaly detection and compliance checking.
        
        Args:
            max_depth: Maximum physically possible trenching depth.
            min_depth: Minimum valid depth (typically 0).
            spike_threshold: Maximum reasonable change between adjacent points.
            window_size: Size of window for rolling statistics.
            std_threshold: Number of standard deviations for outlier detection.
            ignore_anomalies: Whether to exclude anomalous points from compliance analysis.
            
        Returns:
            bool: True if analysis was successful, False otherwise.
        """
        if self.data is None or self.depth_column is None:
            logger.error("Data or depth column not set for analysis")
            return False
            
        # Step 1: Detect anomalies
        logger.info("Starting data analysis pipeline...")
        anomaly_data = self.detect_anomalies(
            max_depth=max_depth,
            min_depth=min_depth,
            spike_threshold=spike_threshold,
            window_size=window_size,
            std_threshold=std_threshold
        )
        
        # Step 2: Check compliance
        self.data = anomaly_data  # Update data with anomaly information
        compliance_data = self.analyze_burial_depth(
            ignore_anomalies=ignore_anomalies
        )
        
        # Step 3: Identify problem sections
        section_data = self.identify_problem_sections()
        
        # Store overall analysis status
        self.analysis_results['analysis_complete'] = True
        
        logger.info("Analysis pipeline completed successfully")
        return True
        
    def detect_anomalies(self, max_depth: float = 3.0, min_depth: float = 0.0, 
                        spike_threshold: float = 0.5, window_size: int = 5, 
                        std_threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect potential anomalies in depth measurements.
        
        Args:
            max_depth: Maximum physically possible trenching depth.
            min_depth: Minimum valid depth (typically 0).
            spike_threshold: Maximum reasonable change between adjacent points.
            window_size: Size of window for rolling statistics.
            std_threshold: Number of standard deviations for outlier detection.
            
        Returns:
            DataFrame with added anomaly detection columns.
        """
        if self.data is None or self.depth_column is None:
            logger.error("Data or depth column not set for anomaly detection")
            return pd.DataFrame()
        
        # Create a copy to avoid modifying original
        result = self.data.copy()
        
        logger.info(f"Detecting anomalies with parameters: max_depth={max_depth}, "
                   f"min_depth={min_depth}, spike_threshold={spike_threshold}")
        
        # Split anomaly detection into separate methods for clarity
        result = self._detect_physical_anomalies(result, max_depth, min_depth)
        result = self._detect_spike_anomalies(result, spike_threshold)
        result = self._detect_statistical_anomalies(result, window_size, std_threshold)
        
        # Combine all anomaly flags
        result['Is_Anomaly'] = (
            result['Exceeds_Max_Depth'] | 
            result['Below_Min_Depth'] | 
            result['Is_Spike'] | 
            result['Is_Outlier']
        )
        
        total_anomalies = result['Is_Anomaly'].sum()
        logger.info(f"Total anomalous points detected: {total_anomalies} "
                   f"({total_anomalies/len(result)*100:.2f}% of data)")
        
        # Determine anomaly type and severity
        result[['Anomaly_Type', 'Anomaly_Severity']] = result.apply(
            self._get_anomaly_info, axis=1, result_type='expand'
        )
        
        # Store results for later use
        self.analysis_results['anomalies'] = result[result['Is_Anomaly']].copy()
        
        return result
    
    def _detect_physical_anomalies(self, data: pd.DataFrame, max_depth: float, 
                                 min_depth: float) -> pd.DataFrame:
        """
        Detect physically impossible depth values.
        
        Args:
            data: DataFrame containing depth measurements.
            max_depth: Maximum physically possible depth.
            min_depth: Minimum valid depth.
            
        Returns:
            DataFrame with added physical anomaly detection columns.
        """
        # Identify physically impossible values
        data['Exceeds_Max_Depth'] = data[self.depth_column] > max_depth
        data['Below_Min_Depth'] = data[self.depth_column] < min_depth
        
        impossible_count = data['Exceeds_Max_Depth'].sum()
        invalid_count = data['Below_Min_Depth'].sum()
        
        logger.info(f"Found {impossible_count} measurements exceeding maximum trenching depth of {max_depth}m")
        logger.info(f"Found {invalid_count} invalid depth measurements (below {min_depth}m)")
        
        return data
    
    def _detect_spike_anomalies(self, data: pd.DataFrame, spike_threshold: float) -> pd.DataFrame:
        """
        Detect sudden changes in depth measurements.
        
        Args:
            data: DataFrame containing depth measurements.
            spike_threshold: Maximum reasonable change between adjacent points.
            
        Returns:
            DataFrame with added spike anomaly detection columns.
        """
        # Calculate changes between adjacent measurements
        data['Depth_Change'] = data[self.depth_column].diff().abs()
        data['Is_Spike'] = data['Depth_Change'] > spike_threshold
        
        spike_count = data['Is_Spike'].sum()
        logger.info(f"Found {spike_count} sudden depth changes exceeding {spike_threshold}m")
        
        return data
    
    def _detect_statistical_anomalies(self, data: pd.DataFrame, window_size: int, 
                                    std_threshold: float) -> pd.DataFrame:
        """
        Detect statistical outliers using rolling window statistics.
        
        Args:
            data: DataFrame containing depth measurements.
            window_size: Size of window for rolling statistics.
            std_threshold: Number of standard deviations for outlier detection.
            
        Returns:
            DataFrame with added statistical anomaly detection columns.
        """
        # Initialize columns with default values
        data['Rolling_Mean'] = data[self.depth_column]
        data['Rolling_Std'] = 0
        data['Z_Score'] = 0
        data['Is_Outlier'] = False
        
        # Handle small datasets gracefully
        if len(data) >= window_size:
            data['Rolling_Mean'] = data[self.depth_column].rolling(
                window=window_size, center=True
            ).mean()
            
            data['Rolling_Std'] = data[self.depth_column].rolling(
                window=window_size, center=True
            ).std()
            
            # Prevent division by zero or comparison with NaN
            data['Rolling_Std'] = data['Rolling_Std'].fillna(0).replace(0, 0.001)
            
            # Mark points that are statistical outliers
            data['Z_Score'] = (data[self.depth_column] - data['Rolling_Mean']) / data['Rolling_Std']
            data['Is_Outlier'] = data['Z_Score'].abs() > std_threshold
            data['Is_Outlier'] = data['Is_Outlier'].fillna(False)
            
            outlier_count = data['Is_Outlier'].sum()
            logger.info(f"Found {outlier_count} statistical outliers (>{std_threshold} std dev from local mean)")
        else:
            logger.info("Dataset too small for statistical outlier detection")
        
        return data
    
    def _get_anomaly_info(self, row: pd.Series) -> pd.Series:
        """
        Helper function to extract anomaly type and severity from a row.
        
        Args:
            row: Series representing a row in the DataFrame.
            
        Returns:
            Series with two values: anomaly type and severity.
        """
        if row['Is_Anomaly']:
            # Determine the type
            if row['Exceeds_Max_Depth']:
                anomaly_type = "Exceeds maximum trenching depth"
                severity = "High"
            elif row['Below_Min_Depth']:
                anomaly_type = "Invalid depth (below minimum)"
                severity = "High"
            elif row['Is_Spike']:
                anomaly_type = f"Sudden depth change ({row['Depth_Change']:.2f}m)"
                severity = "Medium"
            elif row['Is_Outlier']:
                anomaly_type = f"Statistical outlier (z-score: {row['Z_Score']:.2f})"
                severity = "Medium"
            else:
                anomaly_type = "Unknown anomaly"
                severity = "Low"
            
            return pd.Series([anomaly_type, severity])
        else:
            return pd.Series(["", ""])
    
    def analyze_burial_depth(self, ignore_anomalies: bool = False) -> pd.DataFrame:
        """
        Analyze cable burial depth to identify non-compliant sections.
        
        Args:
            ignore_anomalies: Whether to exclude anomalous points from analysis.
            
        Returns:
            DataFrame with added analysis columns.
        """
        if self.data is None or self.depth_column is None:
            logger.error("Data or depth column not set for burial depth analysis")
            return pd.DataFrame()
            
        logger.info(f"Analyzing burial depth compliance against target of {self.target_depth}m...")
        
        # Start with a copy of the data
        result = self.data.copy()
        
        # Filter out anomalous points if requested
        analysis_data = result
        if ignore_anomalies and 'Is_Anomaly' in result.columns:
            anomaly_count = result['Is_Anomaly'].sum()
            if anomaly_count > 0:
                logger.info(f"Ignoring {anomaly_count} anomalous data points in compliance analysis")
                # Create a separate view for analysis
                analysis_data = result[~result['Is_Anomaly']]
            else:
                logger.info("No anomalies found to ignore")
        
        # Mark points that don't meet target depth
        result['Meets_Target'] = result[self.depth_column] >= self.target_depth
        
        # Calculate depth deficit where target isn't met
        result['Depth_Deficit'] = np.where(
            result['Meets_Target'],
            0,
            self.target_depth - result[self.depth_column]
        )
        
        # Calculate percentage of target depth achieved
        result['Target_Percentage'] = (result[self.depth_column] / self.target_depth * 100).round(1)
        
        # Identify the start of non-compliant sections
        result['Section_Start'] = (
            (~result['Meets_Target']) & 
            (result['Meets_Target'].shift(1, fill_value=True) | (result.index == 0))
        )
        
        # Assign unique IDs to each non-compliant section
        result['Section_ID'] = result['Section_Start'].cumsum()
        
        # Clear section IDs for compliant points
        result.loc[result['Meets_Target'], 'Section_ID'] = np.nan
        
        # Calculate compliance statistics
        non_compliant_count = (~result['Meets_Target']).sum()
        compliance_percentage = 100 - (non_compliant_count / len(result) * 100)
        
        logger.info(f"Overall compliance: {compliance_percentage:.2f}% "
                   f"({len(result) - non_compliant_count} of {len(result)} points)")
        
        # Store results for later use
        self.analysis_results['depth_analysis'] = result
        self.analysis_results['compliance_percentage'] = compliance_percentage
        
        return result
    
    def identify_problem_sections(self) -> pd.DataFrame:
        """
        Identify and summarize continuous sections that don't meet depth requirements.
        
        Returns:
            DataFrame summarizing each problem section.
        """
        if 'depth_analysis' not in self.analysis_results:
            logger.error("Burial depth analysis must be run before identifying problem sections")
            return pd.DataFrame()
            
        data = self.analysis_results['depth_analysis']
        
        logger.info("Identifying and analyzing non-compliant sections...")
        
        # Get only the non-compliant points
        non_compliant = data[~data['Meets_Target']].copy()
        
        if len(non_compliant) == 0:
            logger.info("No non-compliant sections found - cable meets requirements")
            self.analysis_results['problem_sections'] = pd.DataFrame()
            return pd.DataFrame()
        
        sections = []
        
        # Group by section ID to analyze each continuous problem area
        section_count = non_compliant['Section_ID'].nunique()
        logger.info(f"Found {section_count} distinct non-compliant sections")
        
        for section_id, group in non_compliant.groupby('Section_ID'):
            if pd.notna(section_id):  # Skip NaN section IDs
                # Determine position reference (KP, position column, or index)
                if self.kp_column and self.kp_column in group.columns:
                    start_pos = group[self.kp_column].min()
                    end_pos = group[self.kp_column].max()
                    length_meters = (end_pos - start_pos) * 1000  # Convert KP to meters
                    position_type = "KP"
                elif self.position_column and self.position_column in group.columns:
                    start_pos = group[self.position_column].min()
                    end_pos = group[self.position_column].max()
                    length_meters = end_pos - start_pos
                    position_type = self.position_column
                else:
                    start_pos = group.index.min()
                    end_pos = group.index.max()
                    length_meters = end_pos - start_pos + 1
                    position_type = "Index"
                
                # Calculate statistics for this section
                min_depth = group[self.depth_column].min()
                max_depth = group[self.depth_column].max()
                avg_depth = group[self.depth_column].mean()
                max_deficit = group['Depth_Deficit'].max()
                
                # Calculate section length in different formats
                if position_type == "KP":
                    length_description = f"{length_meters:.1f}m ({end_pos - start_pos:.3f}km)"
                else:
                    length_description = f"{length_meters:.1f}m"
                
                # Determine severity based on depth deficit
                severity = "High" if max_deficit > 0.5 else \
                          "Medium" if max_deficit > 0.2 else "Low"
                
                # Create section summary
                section = {
                    'Section_ID': int(section_id),
                    'Position_Type': position_type,
                    f'Start_{position_type}': start_pos,
                    f'End_{position_type}': end_pos,
                    'Length': length_description,
                    'Length_Meters': length_meters,
                    'Min_Depth': min_depth,
                    'Max_Depth': max_depth,
                    'Avg_Depth': avg_depth,
                    'Max_Deficit': max_deficit,
                    'Target_Percentage': (min_depth / self.target_depth * 100).round(1),
                    'Severity': severity,
                    'Point_Count': len(group),
                    'Recommendation': self._get_recommendation(max_deficit)
                }
                
                sections.append(section)
        
        # Create DataFrame and sort by severity (most severe first)
        if sections:
            sections_df = pd.DataFrame(sections)
            result = sections_df.sort_values(['Severity', 'Max_Deficit'], 
                                         ascending=[True, False])
            
            # Count by severity
            if 'Severity' in result.columns:
                severity_counts = result['Severity'].value_counts().to_dict()
                for severity, count in severity_counts.items():
                    logger.info(f"  - {severity} severity: {count} section(s)")
                    
            total_length = result['Length_Meters'].sum()
            logger.info(f"Total non-compliant length: {total_length:.1f}m")
            
            # Store results
            self.analysis_results['problem_sections'] = result
            self.analysis_results['total_problem_length'] = total_length
            self.analysis_results['section_count'] = len(result)
            
            return result
        else:
            self.analysis_results['problem_sections'] = pd.DataFrame()
            return pd.DataFrame()
    
    def _get_recommendation(self, depth_deficit: float) -> str:
        """
        Generate a recommendation based on the depth deficit.
        
        Args:
            depth_deficit: The deficit in meters below target depth.
            
        Returns:
            String containing a recommendation.
        """
        if depth_deficit > 0.5:
            return "Requires remedial burial"
        elif depth_deficit > 0.2:
            return "Consider additional protection"
        else:
            return "Monitor during maintenance"
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all analysis results.
        
        Returns:
            Dictionary containing analysis summary.
        """
        if 'analysis_complete' not in self.analysis_results:
            return {'status': 'Analysis not complete'}
            
        summary = {
            'status': 'Analysis complete',
            'data_points': len(self.data) if self.data is not None else 0,
            'target_depth': self.target_depth
        }
        
        # Add anomaly information
        if 'anomalies' in self.analysis_results:
            anomalies = self.analysis_results['anomalies']
            summary['anomaly_count'] = len(anomalies)
            summary['anomaly_percentage'] = (len(anomalies) / len(self.data) * 100) if self.data is not None and len(self.data) > 0 else 0
            
            # Count by severity
            if 'Anomaly_Severity' in anomalies.columns:
                severity_counts = anomalies['Anomaly_Severity'].value_counts().to_dict()
                summary['anomaly_severity_counts'] = severity_counts
        
        # Add compliance information
        if 'compliance_percentage' in self.analysis_results:
            summary['compliance_percentage'] = self.analysis_results['compliance_percentage']
        
        # Add problem section information
        if 'problem_sections' in self.analysis_results:
            problem_sections = self.analysis_results['problem_sections']
            summary['problem_section_count'] = len(problem_sections)
            
            if 'total_problem_length' in self.analysis_results:
                summary['total_problem_length'] = self.analysis_results['total_problem_length']
                
            # Count by severity
            if not problem_sections.empty and 'Severity' in problem_sections.columns:
                severity_counts = problem_sections['Severity'].value_counts().to_dict()
                summary['problem_severity_counts'] = severity_counts
        
        return summary
            
            