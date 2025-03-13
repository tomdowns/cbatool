"""
Base analyzer module for CBAtool.

This module contains the BaseAnalyzer abstract class that defines
the common interface for all analysis types.
"""

from abc import ABC, abstractmethod
import pandas as pd
import logging
from typing import Optional, Dict, List, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers.
    
    Defines the common interface and functionality for different types of analysis
    (depth, position, seabed profile, etc.)
    
    Attributes:
        data (pd.DataFrame): The data to analyze.
        kp_column (str): Name of the column containing KP (kilometer point) values.
        analysis_results (Dict): Dictionary containing results of various analyses.
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize the BaseAnalyzer with optional data.
        
        Args:
            data: DataFrame containing data to analyze (optional).
        """
        self.data = data
        self.kp_column = None
        self.analysis_results = {}
    
    def set_data(self, data: pd.DataFrame) -> bool:
        """
        Set the data to analyze.
        
        Args:
            data: DataFrame containing data to analyze.
            
        Returns:
            bool: True if data was set successfully, False otherwise.
        """
        if data is None or data.empty:
            logger.error("Cannot set empty data for analysis")
            return False
            
        self.data = data
        logger.info(f"Data set for analysis: {len(data)} rows, {len(data.columns)} columns")
        return True
    
    def set_columns(self, kp_column: Optional[str] = None, **kwargs) -> bool:
        """
        Set the column names to use for analysis.
        
        Args:
            kp_column: Name of the column containing KP values.
            **kwargs: Additional column specifications for subclasses.
            
        Returns:
            bool: True if columns were set successfully, False otherwise.
        """
        if self.data is None:
            logger.error("No data loaded for column setting")
            return False
            
        # Set KP column if provided
        if kp_column and kp_column in self.data.columns:
            self.kp_column = kp_column
            logger.info(f"Using KP column: {kp_column}")
        else:
            if kp_column:  # Only log error if a column was specified but not found
                logger.warning(f"KP column '{kp_column}' not found in data")
        
        # Subclasses should implement their specific column setters
        return self._set_specific_columns(**kwargs)
    
    @abstractmethod
    def _set_specific_columns(self, **kwargs) -> bool:
        """
        Set analysis-specific columns.
        
        Args:
            **kwargs: Column specifications specific to the analysis type.
            
        Returns:
            bool: True if columns were set successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def analyze_data(self, **kwargs) -> bool:
        """
        Perform analysis on the data.
        
        Args:
            **kwargs: Analysis parameters specific to the analysis type.
            
        Returns:
            bool: True if analysis was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def identify_problem_sections(self, **kwargs) -> pd.DataFrame:
        """
        Identify continuous sections with issues.
        
        Args:
            **kwargs: Parameters for problem section identification.
            
        Returns:
            DataFrame with problem sections information.
        """
        pass
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of analysis results.
        
        Returns:
            Dictionary containing analysis summary.
        """
        if not self.analysis_results:
            return {'status': 'Analysis not complete'}
            
        # Base summary with common elements
        summary = {
            'status': 'Analysis complete',
            'data_points': len(self.data) if self.data is not None else 0,
            'analysis_type': self._get_analysis_type()
        }
        
        # Add problem section information
        if 'problem_sections' in self.analysis_results:
            problem_sections = self.analysis_results['problem_sections']
            summary['problem_section_count'] = len(problem_sections)
            
            # Count by severity if available
            if not problem_sections.empty and 'Severity' in problem_sections.columns:
                severity_counts = problem_sections['Severity'].value_counts().to_dict()
                summary['problem_severity_counts'] = severity_counts
        
        return summary
    
    def _get_analysis_type(self) -> str:
        """
        Get the type of analysis.
        
        Returns:
            str: Name of the analysis type.
        """
        return "base"