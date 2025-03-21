"""
Depth Analysis Worker for CBAtool v2.0

This module implements the DepthAnalysisWorker, a specialized worker for conducting
depth-related cable burial analysis.
"""

import os
import logging
from typing import Dict, Any, Optional

from ..core.depth_analyzer import DepthAnalyzer
from ..core.visualizer import Visualizer
from ..utils.worker_utils import BaseAnalysisWorker
from ..utils.report_generator import ReportGenerator

# Configure logging
logger = logging.getLogger(__name__)

class DepthAnalysisWorker(BaseAnalysisWorker):
    """
    Specialized worker for conducting depth analysis on cable burial data.
    
    Implements the specific steps of depth analysis workflow while leveraging
    the template method defined in BaseAnalysisWorker.
    """
    
    def __init__(self, app_instance, params: Dict[str, Any]):
        """
        Initialize the DepthAnalysisWorker.
        
        Args:
            app_instance: Reference to the main application instance
            params: Dictionary of parameters for depth analysis
        """
        super().__init__(app_instance, params)
        
        # Validate required parameters
        self._validate_parameters()
        
        # Initialize core analysis components
        self.depth_analyzer = DepthAnalyzer()
        self.visualizer = Visualizer()
        self.report_generator = ReportGenerator(self.output_dir)
    
    def _validate_parameters(self):
        """
        Validate input parameters required for depth analysis.
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        required_params = [
            'file_path', 
            'output_dir', 
            'depth_column', 
            'sheet_name'
        ]
        
        for param in required_params:
            if param not in self.params:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Additional parameter validation can be added here
        if not os.path.exists(self.params['file_path']):
            raise ValueError(f"File not found: {self.params['file_path']}")
    
    def load_data(self):
        """
        Load data from the specified file using the application's data loader.
        
        Loads the data using specified sheet and sets up for analysis.
        """
        print("Loading depth analysis data...")
        
        self.data = self.app.data_loader.load_data(
            sheet_name=self.params.get('sheet_name', '0')
        )
        
        if self.data is None or self.data.empty:
            raise ValueError("Failed to load data from the specified file")
        
        print(f"Loaded {len(self.data)} rows for depth analysis")
    
    def setup_analyzer(self):
        """
        Configure the depth analyzer with selected columns and parameters.
        """
        print("Setting up depth analyzer...")
        
        # Set data for analysis
        self.depth_analyzer.set_data(self.data)
        
        # Set columns
        self.depth_analyzer.set_columns(
            depth_column=self.params['depth_column'],
            kp_column=self.params.get('kp_column'),
            position_column=self.params.get('position_column')
        )
        
        # Set target depth
        target_depth = self.params.get('target_depth', 1.5)
        self.depth_analyzer.set_target_depth(target_depth)
        
        print(f"Analyzer configured with target depth {target_depth}m")
    
    def run_analysis(self):
        """
        Execute the depth analysis process.
        
        Runs the full analysis with configured parameters.
        """
        print("Running depth analysis...")
        
        # Configure analysis parameters from input
        max_depth = self.params.get('max_depth', 3.0)
        ignore_anomalies = self.params.get('ignore_anomalies', False)
        
        # Run analysis
        success = self.depth_analyzer.analyze_data(
            max_depth=max_depth,
            ignore_anomalies=ignore_anomalies
        )
        
        if not success:
            raise RuntimeError("Depth analysis failed")
        
        # Store results for further processing
        self.results['analysis_data'] = self.depth_analyzer.data
        self.results['analysis_summary'] = self.depth_analyzer.get_analysis_summary()
        
        print("Depth analysis completed successfully")
    
    def create_visualization(self):
        """
        Create visualization for the depth analysis results.
        """
        print("Creating depth analysis visualization...")
        
        # Set data for visualization
        self.visualizer.set_data(
            data=self.depth_analyzer.data,
            problem_sections=self.depth_analyzer.analysis_results.get('problem_sections', None)
        )
        
        # Set columns
        self.visualizer.set_columns(
            depth_column=self.params['depth_column'],
            kp_column=self.params.get('kp_column'),
            position_column=self.params.get('position_column')
        )
        
        # Set target depth
        self.visualizer.set_target_depth(
            self.params.get('target_depth', 1.5)
        )
        
        # Create visualization
        segmented = len(self.data) > 5000  # Use segmented view for large datasets
        fig = self.visualizer.create_visualization(
            include_anomalies=True,
            segmented=segmented
        )
        
        if fig is None:
            raise RuntimeError("Failed to create depth analysis visualization")
        
        # Store visualization for output
        self.results['visualization'] = fig
        
        print("Depth analysis visualization created")
    
    def save_outputs(self):
        """
        Save analysis outputs including visualization, Excel reports, and PDF summary.
        """
        print("Saving depth analysis outputs...")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save visualization
        viz_file = os.path.join(self.output_dir, "depth_burial_analysis.html")
        self.visualizer.save_visualization(viz_file)
        print(f"Visualization saved to: {viz_file}")
        
        # Generate comprehensive report
        reports = self.report_generator.create_comprehensive_report(
            self.depth_analyzer.analysis_results,
            viz_file
        )
        
        # Log report locations
        if reports.get('excel_report'):
            print(f"Excel report saved to: {reports['excel_report']}")
        if reports.get('pdf_report'):
            print(f"PDF report saved to: {reports['pdf_report']}")
        
        # Store report paths in results
        self.results['reports'] = reports
        
        print("Depth analysis outputs saved successfully")
