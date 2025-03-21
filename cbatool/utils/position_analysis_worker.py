"""
Position Analysis Worker for CBAtool v2.0

This module implements the PositionAnalysisWorker, a specialized worker for conducting
cable position quality analysis.
"""

import os
import logging
from typing import Dict, Any, Optional

from ..core.position_analyzer import PositionAnalyzer
from ..core.position_visualizer import create_position_dashboard
from ..core.visualizer import Visualizer
from ..utils.worker_utils import BaseAnalysisWorker
from ..utils.report_generator import ReportGenerator

# Configure logging
logger = logging.getLogger(__name__)

class PositionAnalysisWorker(BaseAnalysisWorker):
    """
    Specialized worker for conducting position quality analysis on cable data.
    
    Implements the specific steps of position analysis workflow while leveraging
    the template method defined in BaseAnalysisWorker.
    """
    
    def __init__(self, app_instance, params: Dict[str, Any]):
        """
        Initialize the PositionAnalysisWorker.
        
        Args:
            app_instance: Reference to the main application instance
            params: Dictionary of parameters for position analysis
        """
        super().__init__(app_instance, params)
        
        # Validate required parameters
        self._validate_parameters()
        
        # Initialize core analysis components
        self.position_analyzer = PositionAnalyzer()
        self.visualizer = Visualizer()
        self.report_generator = ReportGenerator(self.output_dir)
    
    def _validate_parameters(self):
        """
        Validate input parameters required for position analysis.
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        required_params = [
            'file_path', 
            'output_dir', 
            'kp_column',
            'sheet_name'
        ]
        
        for param in required_params:
            if param not in self.params:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Additional parameter validation
        if not os.path.exists(self.params['file_path']):
            raise ValueError(f"File not found: {self.params['file_path']}")
    
    def load_data(self):
        """
        Load data from the specified file using the application's data loader.
        
        Loads the data using specified sheet and sets up for analysis.
        """
        print("Loading position analysis data...")
        
        self.data = self.app.data_loader.load_data(
            sheet_name=self.params.get('sheet_name', '0')
        )
        
        if self.data is None or self.data.empty:
            raise ValueError("Failed to load data from the specified file")
        
        print(f"Loaded {len(self.data)} rows for position analysis")
    
    def setup_analyzer(self):
        """
        Configure the position analyzer with selected columns and parameters.
        """
        print("Setting up position analyzer...")
        
        # Set data for analysis
        self.position_analyzer.set_data(self.data)
        
        # Collect optional coordinate columns
        lat_column = self.params.get('lat_column')
        lon_column = self.params.get('lon_column')
        easting_column = self.params.get('easting_column')
        northing_column = self.params.get('northing_column')
        dcc_column = self.params.get('dcc_column')
        
        # Set columns for analysis
        self.position_analyzer.set_columns(
            kp_column=self.params['kp_column'],
            dcc_column=dcc_column,
            lat_column=lat_column,
            lon_column=lon_column,
            easting_column=easting_column,
            northing_column=northing_column
        )
        
        print("Position analyzer configured successfully")
    
    def run_analysis(self):
        """
        Execute the position analysis process.
        
        Runs the full analysis with configured parameters.
        """
        print("Running position analysis...")
        
        # Configure analysis parameters from input
        kp_jump_threshold = self.params.get('kp_jump_threshold', 0.1)
        kp_reversal_threshold = self.params.get('kp_reversal_threshold', 0.0001)
        
        # Run analysis
        success = self.position_analyzer.analyze_data(
            kp_jump_threshold=kp_jump_threshold,
            kp_reversal_threshold=kp_reversal_threshold
        )
        
        if not success:
            raise RuntimeError("Position analysis failed")
        
        # Identify problem segments
        problem_segments = self.position_analyzer.identify_problem_segments()
        
        # Store results for further processing
        self.results['analysis_data'] = self.position_analyzer.data
        self.results['analysis_summary'] = self.position_analyzer.get_analysis_summary()
        self.results['problem_segments'] = problem_segments
        
        print("Position analysis completed successfully")
    
    def create_visualization(self):
        """
        Create visualization for the position analysis results.
        """
        print("Creating position analysis visualization...")
        
        # Determine KP column for visualization
        kp_column = self.params['kp_column']
        
        # Determine DCC column if available
        dcc_column = self.params.get('dcc_column')
        
        # Create dashboard visualization
        fig = self.visualizer.create_position_visualization(
            data=self.position_analyzer.data,
            kp_column=kp_column,
            dcc_column=dcc_column
        )
        
        if fig is None:
            raise RuntimeError("Failed to create position analysis visualization")
        
        # Store visualization for output
        self.results['visualization'] = fig
        
        print("Position analysis visualization created")
    
    def save_outputs(self):
        """
        Save analysis outputs including visualization, Excel reports, and PDF summary.
        """
        print("Saving position analysis outputs...")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save visualization
        viz_file = os.path.join(self.output_dir, "position_quality_analysis.html")
        self.visualizer.save_visualization(viz_file)
        print(f"Visualization saved to: {viz_file}")
        
        # Prepare analysis results for report generation
        analysis_results = self.position_analyzer.analysis_results.copy()
        if 'problem_segments' in self.results:
            analysis_results['problem_sections'] = self.results['problem_segments']
        
        # Generate comprehensive report
        reports = self.report_generator.create_comprehensive_report(
            analysis_results,
            viz_file
        )
        
        # Log report locations
        if reports.get('excel_report'):
            print(f"Excel report saved to: {reports['excel_report']}")
        if reports.get('pdf_report'):
            print(f"PDF report saved to: {reports['pdf_report']}")
        
        # Export position anomalies if they exist
        position_anomalies = self._extract_position_anomalies()
        if position_anomalies is not None and not position_anomalies.empty:
            anomalies_file = os.path.join(self.output_dir, "position_anomalies_report.xlsx")
            position_anomalies.to_excel(anomalies_file, index=False)
            print(f"Position anomalies report saved to: {anomalies_file}")
        
        # Store report paths in results
        self.results['reports'] = reports
        
        print("Position analysis outputs saved successfully")
    
    def _extract_position_anomalies(self):
        """
        Extract anomalous points from position analysis data.
        
        Returns:
            DataFrame of anomalous points or None if no anomalies found
        """
        # Potential anomaly flags
        anomaly_flags = [
            'Is_KP_Jump', 'Is_KP_Reversal', 'Is_KP_Duplicate', 
            'Is_Significant_Deviation'
        ]
        
        # Find existing anomaly flags
        existing_flags = [flag for flag in anomaly_flags if flag in self.position_analyzer.data.columns]
        
        if not existing_flags:
            return None
        
        # Create combined anomaly filter
        anomaly_filter = False
        for flag in existing_flags:
            anomaly_filter |= self.position_analyzer.data[flag]
        
        # Extract anomalous points
        position_anomalies = self.position_analyzer.data[anomaly_filter].copy()
        
        return position_anomalies if not position_anomalies.empty else None
