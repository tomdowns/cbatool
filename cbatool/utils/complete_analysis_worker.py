"""
Complete Analysis Worker for CBAtool v2.0

This module implements the CompleteAnalysisWorker, a specialized worker for conducting
both depth and position analysis sequentially.
"""

import os
import logging
from typing import Dict, Any, Optional

from ..core.depth_analyzer import DepthAnalyzer
from ..core.position_analyzer import PositionAnalyzer
from ..core.visualizer import Visualizer
from ..utils.worker_utils import BaseAnalysisWorker
from ..utils.report_generator import ReportGenerator

# Configure logging
logger = logging.getLogger(__name__)

class CompleteAnalysisWorker(BaseAnalysisWorker):
    """
    Specialized worker for conducting both depth and position analysis sequentially.
    
    Implements the specific steps of a complete analysis workflow while leveraging
    the template method defined in BaseAnalysisWorker.
    """
    
    def __init__(self, app_instance, params: Dict[str, Any]):
        """
        Initialize the CompleteAnalysisWorker.
        
        Args:
            app_instance: Reference to the main application instance
            params: Dictionary of parameters for combined analysis
        """
        super().__init__(app_instance, params)
        
        # Validate required parameters
        self._validate_parameters()
        
        # Initialize core analysis components
        self.depth_analyzer = DepthAnalyzer()
        self.position_analyzer = PositionAnalyzer()
        self.visualizer = Visualizer()
        self.report_generator = ReportGenerator(self.output_dir)
    
    def _validate_parameters(self):
        """
        Validate input parameters required for complete analysis.
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        required_params = [
            'file_path', 
            'output_dir', 
            'depth_column',
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
        print("Loading complete analysis data...")
        
        self.data = self.app.data_loader.load_data(
            sheet_name=self.params.get('sheet_name', '0')
        )
        
        if self.data is None or self.data.empty:
            raise ValueError("Failed to load data from the specified file")
        
        print(f"Loaded {len(self.data)} rows for complete analysis")
    
    def setup_analyzer(self):
        """
        Configure the analyzers with selected columns and parameters.
        """
        print("Setting up analyzers for complete analysis...")
        
        # Set up depth analyzer
        print("Setting up depth analyzer...")
        self.depth_analyzer.set_data(self.data)
        self.depth_analyzer.set_columns(
            depth_column=self.params['depth_column'],
            kp_column=self.params.get('kp_column'),
            position_column=self.params.get('position_column')
        )
        target_depth = self.params.get('target_depth', 1.5)
        self.depth_analyzer.set_target_depth(target_depth)
        print(f"Depth analyzer configured with target depth {target_depth}m")
        
        # Set up position analyzer
        print("Setting up position analyzer...")
        self.position_analyzer.set_data(self.data)
        self.position_analyzer.set_columns(
            kp_column=self.params['kp_column'],
            dcc_column=self.params.get('dcc_column'),
            lat_column=self.params.get('lat_column'),
            lon_column=self.params.get('lon_column'),
            easting_column=self.params.get('easting_column'),
            northing_column=self.params.get('northing_column')
        )
        print("Position analyzer configured successfully")
    
    def run_analysis(self):
        """
        Execute both depth and position analysis processes.
        """
        # 1. Run depth analysis
        print("Running depth analysis...")
        max_depth = self.params.get('max_depth', 3.0)
        ignore_anomalies = self.params.get('ignore_anomalies', False)
        
        depth_success = self.depth_analyzer.analyze_data(
            max_depth=max_depth,
            ignore_anomalies=ignore_anomalies
        )
        
        if not depth_success:
            raise RuntimeError("Depth analysis failed")
        
        print("Depth analysis completed successfully")
        
        # 2. Run position analysis
        print("\nRunning position analysis...")
        kp_jump_threshold = self.params.get('kp_jump_threshold', 0.1)
        kp_reversal_threshold = self.params.get('kp_reversal_threshold', 0.0001)
        
        position_success = self.position_analyzer.analyze_position_data(
            kp_jump_threshold=kp_jump_threshold,
            kp_reversal_threshold=kp_reversal_threshold
        )
        
        if not position_success:
            print("Position analysis failed, but continuing with depth analysis results")
        else:
            print("Position analysis completed successfully")
            
            # Identify problem segments
            problem_sections = self.position_analyzer.identify_problem_sections()
            
            if not problem_sections.empty:
                print(f"Identified {len(problem_sections)} position problem sections")
                self.results['position_problem_sections'] = problem_sections
        
        # Store results for further processing
        self.results['depth_analysis_data'] = self.depth_analyzer.data
        self.results['depth_analysis_summary'] = self.depth_analyzer.get_analysis_summary()
        self.results['position_analysis_data'] = self.position_analyzer.data
        self.results['position_analysis_summary'] = self.position_analyzer.get_analysis_summary()
    
    def create_visualization(self):
        """
        Create visualizations for both depth and position analysis results.
        """
        # 1. Create depth analysis visualization
        print("Creating depth analysis visualization...")
        self.visualizer.set_data(
            data=self.depth_analyzer.data,
            problem_sections=self.depth_analyzer.analysis_results.get('problem_sections', None)
        )
        
        self.visualizer.set_columns(
            depth_column=self.params['depth_column'],
            kp_column=self.params.get('kp_column'),
            position_column=self.params.get('position_column')
        )
        
        self.visualizer.set_target_depth(
            self.params.get('target_depth', 1.5)
        )
        
        # Create depth visualization with segmentation for large datasets
        segmented = len(self.data) > 5000
        depth_fig = self.visualizer.create_visualization(
            include_anomalies=True,
            segmented=segmented
        )
        
        if depth_fig is None:
            raise RuntimeError("Failed to create depth analysis visualization")
        
        self.results['depth_visualization'] = depth_fig
        print("Depth analysis visualization created")
        
        # 2. Create position analysis visualization if position analysis was successful
        if hasattr(self.position_analyzer, 'analysis_results') and self.position_analyzer.analysis_results:
            print("Creating position analysis visualization...")
            position_fig = self.visualizer.create_position_visualization(
                data=self.position_analyzer.data,
                kp_column=self.params['kp_column'],
                dcc_column=self.params.get('dcc_column')
            )
            
            if position_fig is not None:
                self.results['position_visualization'] = position_fig
                print("Position analysis visualization created")
    
    def save_outputs(self):
        """
        Save analysis outputs including visualizations, Excel reports, and PDF summary.
        """
        print("Saving complete analysis outputs...")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 1. Save depth visualization
        depth_viz_file = os.path.join(self.output_dir, "cable_burial_analysis.html")
        self.visualizer.figure = self.results.get('depth_visualization')
        if self.visualizer.figure:
            self.visualizer.save_visualization(depth_viz_file)
            print(f"Depth visualization saved to: {depth_viz_file}")
        
        # 2. Save position visualization if available
        position_viz_file = os.path.join(self.output_dir, "position_quality_analysis.html")
        position_fig = self.results.get('position_visualization')
        if position_fig:
            self.visualizer.figure = position_fig
            self.visualizer.save_visualization(position_viz_file)
            print(f"Position visualization saved to: {position_viz_file}")
        
        # 3. Save Excel reports for depth analysis
        depth_problem_sections = self.depth_analyzer.analysis_results.get('problem_sections')
        if depth_problem_sections is not None and not depth_problem_sections.empty:
            sections_file = os.path.join(self.output_dir, "problem_sections_report.xlsx")
            depth_problem_sections.to_excel(sections_file, index=False)
            print(f"Depth problem sections report saved to: {sections_file}")
        
        depth_anomalies = self.depth_analyzer.analysis_results.get('anomalies')
        if depth_anomalies is not None and not depth_anomalies.empty:
            anomaly_file = os.path.join(self.output_dir, "anomaly_report.xlsx")
            depth_anomalies.to_excel(anomaly_file, index=False)
            print(f"Depth anomalies report saved to: {anomaly_file}")
        
        # 4. Save Excel reports for position analysis
        if 'position_problem_sections' in self.results:
            position_problem_sections = self.results['position_problem_sections']
            if not position_problem_sections.empty:
                pos_sections_file = os.path.join(self.output_dir, "position_problem_sections_report.xlsx")
                position_problem_sections.to_excel(pos_sections_file, index=False)
                print(f"Position problem sections report saved to: {pos_sections_file}")
        
        # 5. Extract and save position anomalies if they exist
        position_anomalies = self._extract_position_anomalies()
        if position_anomalies is not None and not position_anomalies.empty:
            pos_anomalies_file = os.path.join(self.output_dir, "position_anomalies_report.xlsx")
            position_anomalies.to_excel(pos_anomalies_file, index=False)
            print(f"Position anomalies report saved to: {pos_anomalies_file}")
        
        # 6. Generate comprehensive report
        print("\nGenerating comprehensive report...")
        
        # Combine analysis results
        combined_results = self.depth_analyzer.analysis_results.copy()
        
        # Add position analysis results
        if hasattr(self.position_analyzer, 'analysis_results'):
            for key, value in self.position_analyzer.analysis_results.items():
                combined_results[f'position_{key}'] = value
        
        reports = self.report_generator.create_comprehensive_report(
            combined_results,
            depth_viz_file
        )
        
        # Log report locations
        if reports.get('excel_report'):
            print(f"Comprehensive Excel report saved to: {reports['excel_report']}")
        if reports.get('pdf_report'):
            print(f"PDF summary report saved to: {reports['pdf_report']}")
        
        # Store report paths in results
        self.results['reports'] = reports
        
        print("Complete analysis outputs saved successfully")
    
    def _extract_position_anomalies(self):
        """
        Extract anomalous points from position analysis data.
        
        Returns:
            DataFrame of anomalous points or None if no anomalies found
        """
        # Check if position analyzer has analysis results
        if not hasattr(self.position_analyzer, 'data') or self.position_analyzer.data is None:
            return None
        
        # Potential anomaly flags
        anomaly_flags = [
            'Is_KP_Jump', 'Is_KP_Reversal', 'Is_KP_Duplicate', 
            'Is_Significant_Deviation'
        ]
        
        # Find existing anomaly flags
        existing_flags = [flag for flag in anomaly_flags 
                         if flag in self.position_analyzer.data.columns]
        
        if not existing_flags:
            return None
        
        # Create combined anomaly filter
        import pandas as pd
        anomaly_filter = pd.Series(False, index=self.position_analyzer.data.index)
        for flag in existing_flags:
            anomaly_filter |= self.position_analyzer.data[flag]
        
        # Add position quality check if available
        if 'Position_Quality' in self.position_analyzer.data.columns:
            anomaly_filter |= (self.position_analyzer.data['Position_Quality'] != 'Good')
        
        # Extract anomalous points
        position_anomalies = self.position_analyzer.data[anomaly_filter].copy()
        
        return position_anomalies if not position_anomalies.empty else None
