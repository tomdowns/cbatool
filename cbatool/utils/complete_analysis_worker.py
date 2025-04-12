# -*- coding: utf-8 -*-
"""
Complete Analysis Worker for CBAtool v2.0

This module implements the CompleteAnalysisWorker, a specialized worker for conducting
both depth and position analysis sequentially and producing a unified standardized result.
"""

import os
import logging
import pandas as pd # Keep pandas import for _extract_position_anomalies if still needed
from typing import Dict, Any, Optional
from datetime import datetime # Needed for timestamp

# Core components
from ..core.depth_analyzer import DepthAnalyzer
from ..core.position_analyzer import PositionAnalyzer
from ..core.visualizer import Visualizer
# Utilities
from ..utils.worker_utils import BaseAnalysisWorker
from ..utils.report_generator import ReportGenerator

# Configure logging
logger = logging.getLogger(__name__)

class CompleteAnalysisWorker(BaseAnalysisWorker):
    """
    Specialized worker for conducting both depth and position analysis sequentially.

    Implements the specific steps of a complete analysis workflow, generates
    a unified standardized result dictionary, and triggers report generation.
    Leverages the template method defined in BaseAnalysisWorker for the overall run flow.
    """

    def __init__(self, app_instance, params: Dict[str, Any]):
        """
        Initialize the CompleteAnalysisWorker.

        Args:
            app_instance: Reference to the main application instance (for UI updates).
            params: Dictionary of parameters for combined analysis.
        """
        super().__init__(app_instance, params) # Calls BaseAnalysisWorker.__init__

        # Validate required parameters early
        self._validate_parameters()

        # Initialize core analysis components
        self.depth_analyzer = DepthAnalyzer()
        self.position_analyzer = PositionAnalyzer()
        self.visualizer = Visualizer() # Used for depth viz
        # Note: Position viz might be handled differently or within PositionAnalyzer/Visualizer
        self.report_generator = ReportGenerator(
            self.output_dir,
            # Pass report config from main config if available
            report_config=self.params.get('report_config', {})
        )

        # Store viz file paths generated during the run
        self.depth_viz_file_path: Optional[str] = None
        self.position_viz_file_path: Optional[str] = None

    def _validate_parameters(self):
        """Validate input parameters required for complete analysis."""
        required_params = [
            'file_path',
            'output_dir',
            'depth_column',
            'kp_column',
            'sheet_name'
        ]
        missing = [p for p in required_params if p not in self.params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        if not os.path.exists(self.params['file_path']):
            raise ValueError(f"Input file not found: {self.params['file_path']}")
        # Add more validation as needed (e.g., check if columns exist after loading)

    def load_data(self):
        """Load data using the application's data loader."""
        self.set_progress(5, "Loading data...")
        print(f"Loading data from: {self.params['file_path']} Sheet: {self.params.get('sheet_name', '0')}")
        self.data = self.app.data_loader.load_data(
            sheet_name=self.params.get('sheet_name', '0')
        )
        if self.data is None or self.data.empty:
            raise ValueError("Failed to load data or data is empty.")
        print(f"Loaded {len(self.data)} rows.")
        self.set_progress(10, "Data loaded.")


    def setup_analyzer(self):
        """Configure both depth and position analyzers."""
        self.set_progress(15, "Configuring analyzers...")
        if self.data is None: # Should not happen if load_data succeeded
             raise RuntimeError("Data not loaded before setting up analyzer.")

        # --- Configure Depth Analyzer ---
        print("Configuring depth analyzer...")
        self.depth_analyzer.set_data(self.data.copy()) # Give each analyzer its own copy? Or ensure they don't modify inplace? Using copy for safety.
        depth_cols_set = self.depth_analyzer.set_columns(
            depth_column=self.params['depth_column'],
            kp_column=self.params.get('kp_column'),
            # position_column=self.params.get('position_column') # Pass relevant cols only
        )
        if not depth_cols_set:
             raise ValueError("Failed to set required columns for Depth Analyzer.")
        target_depth = self.params.get('target_depth', 1.5)
        self.depth_analyzer.set_target_depth(target_depth)
        print(f"Depth analyzer configured: Target Depth={target_depth}m")

        # --- Configure Position Analyzer ---
        print("Configuring position analyzer...")
        self.position_analyzer.set_data(self.data.copy()) # Use copy for safety
        pos_cols_set = self.position_analyzer.set_columns(
            kp_column=self.params['kp_column'],
            # Pass only relevant optional columns
            # dcc_column=self.params.get('dcc_column'), # If DCC is used
            lat_column=self.params.get('lat_column'),
            lon_column=self.params.get('lon_column'),
            easting_column=self.params.get('easting_column'),
            northing_column=self.params.get('northing_column')
        )
        if not pos_cols_set:
             # Position analysis might be optional if only KP is required?
             # Or raise ValueError("Failed to set required columns for Position Analyzer.")
             print("Warning: Could not set all expected columns for Position Analyzer.")

        print("Position analyzer configured.")
        self.set_progress(20, "Analyzers configured.")

    def run_analysis(self):
        """Execute both depth and position analysis processes."""
        # --- Run Depth Analysis ---
        self.set_progress(25, "Running depth analysis...")
        print("Running depth analysis...")
        depth_config = self.params.get('depth_config', {}) # Get depth-specific config
        depth_success = self.depth_analyzer.analyze_data(
            max_depth=self.params.get('max_depth', 3.0), # Still pass main params
            ignore_anomalies=self.params.get('ignore_anomalies', False),
            # Pass other params from depth_config if needed by analyze_data
            # e.g., spike_threshold=depth_config.get('spikeThreshold')
        )
        if not depth_success:
            # Decide how to handle failure: exception or warning?
            raise RuntimeError("Core depth analysis failed.")
        print("Depth analysis completed.")
        self.set_progress(50, "Depth analysis complete.")

        # --- Run Position Analysis ---
        self.set_progress(55, "Running position analysis...")
        print("\nRunning position analysis...")
        position_config = self.params.get('position_config', {}) # Get position-specific config
        position_success = self.position_analyzer.analyze_position_data(
            # Pass parameters from position_config
            kp_jump_threshold=position_config.get('kpJumpThreshold', 0.1),
            kp_reversal_threshold=position_config.get('kpReversalThreshold', 0.0001),
            # dcc_threshold=position_config.get('dccThreshold', 5.0) # If DCC used
        )
        if not position_success:
            # Log warning but continue, as depth results might still be useful
            logger.warning("Position analysis failed or produced no results. Continuing...")
            print("Warning: Position analysis failed or produced no results.")
        else:
            print("Position analysis completed.")
        self.set_progress(80, "Position analysis complete.")

        # Note: Storing intermediate results in self.results is handled by BaseAnalysisWorker's template method

    def create_visualization(self):
        """Create visualizations for both depth and position analysis."""
        # Visualization parameters from config
        viz_config = self.params.get('visualization_config', {})
        use_segmented = viz_config.get('useSegmented', len(self.data) > 5000) # Default based on size
        include_anom = viz_config.get('includeAnomalies', True)

        # --- Create Depth Visualization ---
        self.set_progress(85, "Creating depth visualization...")
        print("Creating depth visualization...")
        try:
            # Ensure visualizer has the correct data from the depth analyzer
            self.visualizer.set_data(
                data=self.depth_analyzer.data,
                # Pass problem sections directly if analyze_data populates them,
                # otherwise they might be generated later via get_standardized_results
                problem_sections=self.depth_analyzer.analysis_results.get('problem_sections')
            )
            self.visualizer.set_columns(
                depth_column=self.params['depth_column'],
                kp_column=self.params.get('kp_column'),
                position_column=self.params.get('position_column')
            )
            self.visualizer.set_target_depth(self.params.get('target_depth', 1.5))

            depth_fig = self.visualizer.create_visualization(
                include_anomalies=include_anom,
                segmented=use_segmented
            )
            if depth_fig is None:
                logger.error("Failed to create depth analysis visualization object.")
                print("Error: Failed to create depth visualization.")
            else:
                # Store figure temporarily if needed, but focus on saving path
                self.depth_viz_file_path = os.path.join(self.output_dir, "cable_burial_analysis.html")
                self.visualizer.figure = depth_fig # Set figure for saving
                if self.visualizer.save_visualization(self.depth_viz_file_path):
                     print(f"Depth visualization saved to: {self.depth_viz_file_path}")
                else:
                     print("Error: Failed to save depth visualization.")
                     self.depth_viz_file_path = None # Mark as failed

        except Exception as e:
            logger.error("Error creating/saving depth visualization", exc_info=True)
            print(f"Error during depth visualization: {e}")

        # --- Create Position Visualization ---
        self.set_progress(90, "Creating position visualization...")
        print("Creating position visualization...")
        try:
            # Check if position analysis actually produced data
            if hasattr(self.position_analyzer, 'data') and self.position_analyzer.data is not None:
                # Use the main visualizer instance to call the position-specific plot
                position_fig = self.visualizer.create_position_visualization(
                    data=self.position_analyzer.data,
                    kp_column=self.params['kp_column'],
                    # Pass relevant columns used by position viz
                    # dcc_column=self.params.get('dcc_column')
                )
                if position_fig is not None:
                    self.position_viz_file_path = os.path.join(self.output_dir, "position_quality_analysis.html")
                    self.visualizer.figure = position_fig # Set figure for saving
                    if self.visualizer.save_visualization(self.position_viz_file_path):
                         print(f"Position visualization saved to: {self.position_viz_file_path}")
                    else:
                         print("Error: Failed to save position visualization.")
                         self.position_viz_file_path = None # Mark as failed
                else:
                    logger.warning("Failed to create position visualization object.")
                    print("Warning: Failed to create position visualization.")
            else:
                 logger.warning("Skipping position visualization: No position analysis data available.")
                 print("Skipping position visualization: No data.")

        except Exception as e:
            logger.error("Error creating/saving position visualization", exc_info=True)
            print(f"Error during position visualization: {e}")

        self.set_progress(95, "Visualizations created.")

    # --- NEW METHOD ---
    def get_standardized_results(self) -> Dict[str, Any]:
        """
        Combine results from depth and position analyzers into a single standardized dict.

        Returns:
            Dictionary conforming to the unified reporting standard.
        """
        print("Standardizing results...")
        # Ensure analyzers have run and have the method (requires BaseAnalyzer inheritance)
        if not hasattr(self.depth_analyzer, 'get_standardized_results'):
             raise AttributeError("DepthAnalyzer missing 'get_standardized_results' method.")
        if not hasattr(self.position_analyzer, 'get_standardized_results'):
             raise AttributeError("PositionAnalyzer missing 'get_standardized_results' method.")

        # Get standardized results from each analyzer
        # Add error handling in case one analysis failed partially
        try:
            depth_standardized = self.depth_analyzer.get_standardized_results()
        except Exception as e:
            logger.error("Failed to get standardized results from DepthAnalyzer", exc_info=True)
            print(f"Error getting depth results: {e}")
            depth_standardized = {"analysis_type": "depth", "error": str(e)} # Include error marker

        try:
            position_standardized = self.position_analyzer.get_standardized_results()
        except Exception as e:
            logger.error("Failed to get standardized results from PositionAnalyzer", exc_info=True)
            print(f"Error getting position results: {e}")
            position_standardized = {"analysis_type": "position", "error": str(e)} # Include error marker


        # --- Create the Combined Structure ---
        complete_standardized = {
            "analysis_type": "complete",
            "timestamp": datetime.now().isoformat(), # Use ISO format string
            "config_name": self.params.get('config_name', 'Custom'), 
            "input_file": os.path.basename(self.params.get('file_path', 'N/A')),
            "cable_id": self.params.get('cable_id'), # Include cable ID if provided

            # Nest the results
            "depth_results": depth_standardized,
            "position_results": position_standardized,

            # Add overall summary (example)
            "overall_summary": {
                "data_points": len(self.data) if self.data is not None else 0,
                # Add other useful top-level info if desired
                "kp_range_processed": self.position_analyzer.analysis_results.get('kp_range', None) # Example
            },

            # Combine recommendations (simple concatenation example)
            "combined_recommendations": (
                depth_standardized.get("recommendations", []) +
                position_standardized.get("recommendations", [])
            ),

            # Add references to generated visualization files
            "visualization_references": {
                "depth_analysis": os.path.basename(self.depth_viz_file_path) if self.depth_viz_file_path else None,
                "position_analysis": os.path.basename(self.position_viz_file_path) if self.position_viz_file_path else None,
            }
        }
        print("Results standardized.")
        return complete_standardized

    def save_outputs(self):
        """
        Generate and save the comprehensive report using standardized results.
        """
        # Note: Visualizations are now saved in create_visualization step.
        # This method now focuses on generating the data reports.
        self.set_progress(96, "Generating reports...")
        print("\nGenerating comprehensive data reports...")

       
        # --- Get Standardized Results ---
        try:
            standardized_results = self.get_standardized_results()
        except Exception as e:
             logger.error("Failed to generate standardized results for reporting.", exc_info=True)
             print(f"Error: Could not generate standardized results: {e}")
             self.update_ui_status("Reporting failed: Error getting results.")
             # Update main results dict to show failure?
             self.results['reporting_error'] = str(e)
             return # Cannot proceed with reporting

        # --- Generate Reports using ReportGenerator ---
        try:
            reports = self.report_generator.create_comprehensive_report(
                standardized_results, # Pass the single standardized dictionary
                # Pass viz paths separately if needed by reporter (e.g., for linking)
                visualization_paths={
                     'depth': self.depth_viz_file_path,
                     'position': self.position_viz_file_path
                }
            )

            # Log report locations from the dictionary returned by the reporter
            if reports: # Check if reports dict was returned
                excel_path = reports.get('excel_report')
                pdf_path = reports.get('pdf_report')
                if excel_path:
                    print(f"Comprehensive Excel report saved to: {excel_path}")
                if pdf_path:
                    print(f"PDF summary report saved to: {pdf_path}")
                # Store paths in main results dict
                self.results['report_paths'] = reports
            else:
                 print("Warning: Report generator did not return report paths.")


            print("Report generation complete.")
            self.set_progress(100, "Reporting complete.")

        except Exception as e:
            logger.error("Failed during report generation", exc_info=True)
            print(f"Error: Failed to generate reports: {e}")
            self.update_ui_status("Reporting failed.")
            self.results['reporting_error'] = str(e)


    def _extract_position_anomalies(self):
        """
        DEPRECATED: Extracts anomalous points from position analysis data.
        This logic should now ideally be part of PositionAnalyzer's
        get_standardized_results or handled by the ReportGenerator based on
        standardized anomaly details. Keeping for reference if needed temporarily.
        """
        logger.warning("_extract_position_anomalies is deprecated.")
        # ... (original code - consider removing if ReportGenerator handles it) ...
        if not hasattr(self.position_analyzer, 'data') or self.position_analyzer.data is None:
            return None
        anomaly_flags = ['Is_KP_Jump', 'Is_KP_Reversal', 'Is_KP_Duplicate', 'Is_Significant_Deviation']
        existing_flags = [flag for flag in anomaly_flags if flag in self.position_analyzer.data.columns]
        if not existing_flags: return None
        anomaly_filter = pd.Series(False, index=self.position_analyzer.data.index)
        for flag in existing_flags:
            # Ensure boolean comparison works even if column contains non-boolean data
            try:
                 anomaly_filter |= self.position_analyzer.data[flag].astype(bool)
            except:
                 logger.warning(f"Could not process anomaly flag column {flag}")
                 continue # Skip problematic flag

        if 'Position_Quality' in self.position_analyzer.data.columns:
             try:
                  anomaly_filter |= (self.position_analyzer.data['Position_Quality'] != 'Good')
             except:
                  logger.warning("Could not process Position_Quality column")

        position_anomalies = self.position_analyzer.data.loc[anomaly_filter].copy()
        return position_anomalies if not position_anomalies.empty else None