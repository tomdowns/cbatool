"""
Test module for position analysis worker.

This module contains tests for the PositionAnalysisWorker class.
"""

import os
import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Use absolute imports instead of relative imports
from cbatool.utils.position_analysis_worker import PositionAnalysisWorker
from cbatool.core.position_analyzer import PositionAnalyzer
from cbatool.core.visualizer import Visualizer


class TestPositionAnalysisWorker(unittest.TestCase):
    """Test cases for the PositionAnalysisWorker class."""
    
    @patch('os.path.exists', return_value=True)  # Mock file existence check
    def setUp(self, mock_exists):
        """Set up test fixtures."""
        # Create a mock app instance
        self.mock_app = MagicMock()
        self.mock_app.redirector = MagicMock()
        self.mock_app.data_loader = MagicMock()
        
        # Create test data
        self.test_data = pd.DataFrame({
            'KP': np.linspace(0, 10, 100),
            'DCC': np.random.uniform(-5.0, 5.0, 100),
            'Lat': np.random.uniform(50.0, 51.0, 100),
            'Lon': np.random.uniform(-1.0, 0.0, 100)
        })
        
        # Mock the data loader to return test data
        self.mock_app.data_loader.load_data.return_value = self.test_data
        
        # Create test parameters
        self.test_params = {
            'file_path': 'test_file.csv',
            'output_dir': 'test_output',
            'kp_column': 'KP',
            'dcc_column': 'DCC',
            'lat_column': 'Lat',
            'lon_column': 'Lon',
            'sheet_name': '0'
        }
        
        # Create the worker
        self.worker = PositionAnalysisWorker(self.mock_app, self.test_params)
    
    def test_position_worker(self):
        """Basic test for the PositionAnalysisWorker."""
        # Test that initialization was successful
        self.assertIsInstance(self.worker.position_analyzer, PositionAnalyzer)
        self.assertIsInstance(self.worker.visualizer, Visualizer)
        self.assertEqual(self.worker.params, self.test_params)
    
    def test_run_position_analysis(self):
        """Test the entire position analysis workflow."""
        # Mock the worker methods
        self.worker.load_data = MagicMock()
        self.worker.setup_analyzer = MagicMock()
        self.worker.run_analysis = MagicMock()
        self.worker.create_visualization = MagicMock()
        self.worker.save_outputs = MagicMock()
        self.worker.update_ui_status = MagicMock()
        
        # Run the worker through the base class run method
        self.worker.run()
        
        # Verify all methods were called in sequence
        self.worker.load_data.assert_called_once()
        self.worker.setup_analyzer.assert_called_once()
        self.worker.run_analysis.assert_called_once()
        self.worker.create_visualization.assert_called_once()
        self.worker.save_outputs.assert_called_once()
        self.worker.update_ui_status.assert_called_once()
    
    def test_analyze_position_data_call(self):
        """Test that the worker correctly calls the analyze_position_data method."""
        # Mock the position_analyzer
        self.worker.position_analyzer = MagicMock()
        self.worker.position_analyzer.analyze_position_data.return_value = True
        self.worker.position_analyzer.identify_problem_segments.return_value = pd.DataFrame()
        
        # Run the analysis
        self.worker.run_analysis()
        
        # Verify that analyze_position_data was called (not analyze_data)
        self.worker.position_analyzer.analyze_position_data.assert_called_once()


if __name__ == '__main__':
    unittest.main()
