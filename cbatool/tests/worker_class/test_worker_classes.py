"""
Test module for CBAtool worker classes.

This module contains comprehensive tests for the worker classes in CBAtool,
including DepthAnalysisWorker, PositionAnalysisWorker, and related functionality.
"""

import os
import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Import the worker classes to test
from cbatool.utils.worker_utils import BaseAnalysisWorker
from cbatool.utils.depth_analysis_worker import DepthAnalysisWorker
from cbatool.utils.position_analysis_worker import PositionAnalysisWorker

# Import analyzer classes
from cbatool.core.depth_analyzer import DepthAnalyzer
from cbatool.core.position_analyzer import PositionAnalyzer


class TestBaseAnalysisWorker(unittest.TestCase):
    """Test cases for the BaseAnalysisWorker class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock app instance
        self.mock_app = MagicMock()
        self.mock_app.redirector = MagicMock()
        
        # Create test parameters
        self.test_params = {
            'file_path': 'test_file.csv',
            'output_dir': 'test_output'
        }
        
        # Create a concrete subclass of BaseAnalysisWorker for testing
        class ConcreteWorker(BaseAnalysisWorker):
            def load_data(self):
                return True
                
            def setup_analyzer(self):
                return True
                
            def run_analysis(self):
                return True
                
            def create_visualization(self):
                return True
                
            def save_outputs(self):
                return True
        
        self.worker = ConcreteWorker(self.mock_app, self.test_params)
    
    def test_initialization(self):
        """Test worker initialization."""
        self.assertEqual(self.worker.app, self.mock_app)
        self.assertEqual(self.worker.params, self.test_params)
        self.assertEqual(self.worker.output_dir, self.test_params['output_dir'])
        self.assertEqual(self.worker.results, {})
    
    def test_run_method(self):
        """Test the run method calls all required steps."""
        # Mock the required methods
        self.worker.load_data = MagicMock()
        self.worker.setup_analyzer = MagicMock()
        self.worker.run_analysis = MagicMock()
        self.worker.create_visualization = MagicMock()
        self.worker.save_outputs = MagicMock()
        self.worker.update_ui_status = MagicMock()
        
        # Run the worker
        self.worker.run()
        
        # Verify all methods were called
        self.worker.load_data.assert_called_once()
        self.worker.setup_analyzer.assert_called_once()
        self.worker.run_analysis.assert_called_once()
        self.worker.create_visualization.assert_called_once()
        self.worker.save_outputs.assert_called_once()
        self.worker.update_ui_status.assert_called_once()

    def test_handle_exception(self):
        """Test exception handling."""
        # Mock the app's set_status method
        self.mock_app.set_status = MagicMock()
        
        # Set up a test exception
        test_exception = ValueError("Test exception")
        
        # Call the handle_exception method
        self.worker.handle_exception(test_exception)
        
        # Verify the app's set_status method was called
        self.mock_app.set_status.assert_called_once_with("Analysis failed")


class TestDepthAnalysisWorker(unittest.TestCase):
    """Test cases for the DepthAnalysisWorker class."""
    
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
            'Depth': np.random.uniform(1.0, 2.0, 100),
            'Position': np.arange(100)
        })
        
        # Mock the data loader to return test data
        self.mock_app.data_loader.load_data.return_value = self.test_data
        
        # Create test parameters
        self.test_params = {
            'file_path': 'test_file.csv',
            'output_dir': 'test_output',
            'depth_column': 'Depth',
            'kp_column': 'KP',
            'position_column': 'Position',
            'sheet_name': '0',
            'target_depth': 1.5,
            'max_depth': 3.0,
            'ignore_anomalies': False
        }
        
        # Create the worker
        self.worker = DepthAnalysisWorker(self.mock_app, self.test_params)
    
    def test_initialization(self):
        """Test DepthAnalysisWorker initialization."""
        self.assertEqual(self.worker.app, self.mock_app)
        self.assertEqual(self.worker.params, self.test_params)
        self.assertEqual(self.worker.output_dir, self.test_params['output_dir'])
        self.assertIsInstance(self.worker.depth_analyzer, DepthAnalyzer)
        self.assertIsNotNone(self.worker.visualizer)
        self.assertIsNotNone(self.worker.report_generator)
    
    @patch('os.path.exists', return_value=True)  # Mock file existence check
    def test_validate_parameters(self, mock_exists):
        """Test parameter validation."""
        # Should work with valid parameters
        self.worker._validate_parameters()  # Should not raise exceptions
        
        # Test with missing required parameter
        invalid_params = self.test_params.copy()
        del invalid_params['depth_column']
        
        worker = DepthAnalysisWorker(self.mock_app, invalid_params)
        with self.assertRaises(ValueError):
            worker._validate_parameters()
    
    @patch('os.makedirs')
    def test_load_data(self, mock_makedirs):
        """Test the load_data method."""
        # Run the method
        self.worker.load_data()
        
        # Check that the data loader was called correctly
        self.mock_app.data_loader.load_data.assert_called_once_with(
            sheet_name=self.test_params['sheet_name']
        )
        
        # Check that the data was set correctly
        self.assertEqual(self.worker.data.equals(self.test_data), True)
    
    def test_setup_analyzer(self):
        """Test the setup_analyzer method."""
        # Mock the depth_analyzer methods
        self.worker.depth_analyzer.set_data = MagicMock()
        self.worker.depth_analyzer.set_columns = MagicMock()
        self.worker.depth_analyzer.set_target_depth = MagicMock()
        
        # Set test data
        self.worker.data = self.test_data
        
        # Run the method
        self.worker.setup_analyzer()
        
        # Check that the analyzer methods were called correctly
        self.worker.depth_analyzer.set_data.assert_called_once_with(self.test_data)
        self.worker.depth_analyzer.set_columns.assert_called_once_with(
            depth_column=self.test_params['depth_column'],
            kp_column=self.test_params['kp_column'],
            position_column=self.test_params['position_column']
        )
        self.worker.depth_analyzer.set_target_depth.assert_called_once_with(
            self.test_params['target_depth']
        )
    
    def test_run_analysis(self):
        """Test the run_analysis method."""
        # Mock the depth_analyzer methods
        self.worker.depth_analyzer.analyze_data = MagicMock(return_value=True)
        self.worker.depth_analyzer.data = self.test_data
        self.worker.depth_analyzer.analysis_results = {'key': 'value'}
        self.worker.depth_analyzer.get_analysis_summary = MagicMock(return_value={'summary': 'test'})
        
        # Run the method
        self.worker.run_analysis()
        
        # Check that the analyzer methods were called correctly
        self.worker.depth_analyzer.analyze_data.assert_called_once_with(
            max_depth=self.test_params['max_depth'],
            ignore_anomalies=self.test_params['ignore_anomalies']
        )
        
        # Check that the results were stored correctly
        self.assertEqual(self.worker.results['analysis_data'].equals(self.test_data), True)
        self.assertEqual(self.worker.results['analysis_summary'], {'summary': 'test'})
    
    def test_create_visualization(self):
        """Test the create_visualization method."""
        # Mock the visualizer methods
        self.worker.visualizer.set_data = MagicMock()
        self.worker.visualizer.set_columns = MagicMock()
        self.worker.visualizer.set_target_depth = MagicMock()
        self.worker.visualizer.create_visualization = MagicMock()
        
        # Set test data and analysis results
        self.worker.data = self.test_data
        self.worker.depth_analyzer.analysis_results = {'problem_sections': pd.DataFrame()}
        
        # Run the method
        self.worker.create_visualization()
        
        # Check that the visualizer methods were called correctly
        self.worker.visualizer.set_data.assert_called_once()
        self.worker.visualizer.set_columns.assert_called_once()
        self.worker.visualizer.set_target_depth.assert_called_once()
        self.worker.visualizer.create_visualization.assert_called_once()
    
    @patch('os.makedirs')
    def test_save_outputs(self, mock_makedirs):
        """Test the save_outputs method."""
        # Mock the visualizer and report generator methods
        self.worker.visualizer.save_visualization = MagicMock()
        self.worker.report_generator.create_comprehensive_report = MagicMock(
            return_value={'excel_report': 'test.xlsx', 'pdf_report': 'test.pdf'}
        )
        
        # Mock results
        self.worker.results['visualization'] = MagicMock()
        self.worker.depth_analyzer.analysis_results = {'key': 'value'}
        
        # Run the method
        self.worker.save_outputs()
        
        # Check that the methods were called correctly
        mock_makedirs.assert_called_once_with(self.test_params['output_dir'], exist_ok=True)
        self.worker.visualizer.save_visualization.assert_called_once()
        self.worker.report_generator.create_comprehensive_report.assert_called_once()
        
        # Check that the report paths were stored
        self.assertEqual(self.worker.results['reports'], 
                         {'excel_report': 'test.xlsx', 'pdf_report': 'test.pdf'})


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
            'Lon': np.random.uniform(-1.0, 0.0, 100),
            'Easting': np.random.uniform(500000, 510000, 100),
            'Northing': np.random.uniform(100000, 110000, 100)
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
            'easting_column': 'Easting',
            'northing_column': 'Northing',
            'sheet_name': '0'
        }
        
        # Create the worker
        self.worker = PositionAnalysisWorker(self.mock_app, self.test_params)
    
    def test_initialization(self):
        """Test PositionAnalysisWorker initialization."""
        self.assertEqual(self.worker.app, self.mock_app)
        self.assertEqual(self.worker.params, self.test_params)
        self.assertEqual(self.worker.output_dir, self.test_params['output_dir'])
        self.assertIsInstance(self.worker.position_analyzer, PositionAnalyzer)
        self.assertIsNotNone(self.worker.visualizer)
        self.assertIsNotNone(self.worker.report_generator)
    
    @patch('os.path.exists', return_value=True)  # Mock file existence check
    def test_validate_parameters(self, mock_exists):
        """Test parameter validation."""
        # Should work with valid parameters
        self.worker._validate_parameters()  # Should not raise exceptions
        
        # Test with missing required parameter
        invalid_params = self.test_params.copy()
        del invalid_params['kp_column']
        
        worker = PositionAnalysisWorker(self.mock_app, invalid_params)
        with self.assertRaises(ValueError):
            worker._validate_parameters()
    
    @patch('os.makedirs')
    def test_load_data(self, mock_makedirs):
        """Test the load_data method."""
        # Run the method
        self.worker.load_data()
        
        # Check that the data loader was called correctly
        self.mock_app.data_loader.load_data.assert_called_once_with(
            sheet_name=self.test_params['sheet_name']
        )
        
        # Check that the data was set correctly
        self.assertEqual(self.worker.data.equals(self.test_data), True)
    
    def test_setup_analyzer(self):
        """Test the setup_analyzer method."""
        # Mock the position_analyzer methods
        self.worker.position_analyzer.set_data = MagicMock()
        self.worker.position_analyzer.set_columns = MagicMock()
        
        # Set test data
        self.worker.data = self.test_data
        
        # Run the method
        self.worker.setup_analyzer()
        
        # Check that the analyzer methods were called correctly
        self.worker.position_analyzer.set_data.assert_called_once_with(self.test_data)
        self.worker.position_analyzer.set_columns.assert_called_once_with(
            kp_column=self.test_params['kp_column'],
            dcc_column=self.test_params['dcc_column'],
            lat_column=self.test_params['lat_column'],
            lon_column=self.test_params['lon_column'],
            easting_column=self.test_params['easting_column'],
            northing_column=self.test_params['northing_column']
        )
    
    def test_run_analysis(self):
        """Test the run_analysis method."""
        # Mock the position_analyzer methods
        # Note: This is where we're testing for the correct method name
        self.worker.position_analyzer.analyze_position_data = MagicMock(return_value=True)
        self.worker.position_analyzer.identify_problem_segments = MagicMock(return_value=pd.DataFrame())
        self.worker.position_analyzer.data = self.test_data
        self.worker.position_analyzer.analysis_results = {'key': 'value'}
        self.worker.position_analyzer.get_analysis_summary = MagicMock(return_value={'summary': 'test'})
        
        # Run the method
        self.worker.run_analysis()
        
        # Check that the analyzer methods were called correctly
        self.worker.position_analyzer.analyze_position_data.assert_called_once()
        
        # Check that the results were stored correctly
        self.assertEqual(self.worker.results['analysis_data'].equals(self.test_data), True)
        self.assertEqual(self.worker.results['analysis_summary'], {'summary': 'test'})
    
    def test_create_visualization(self):
        """Test the create_visualization method."""
        # Mock the visualizer methods
        self.worker.visualizer.create_position_visualization = MagicMock()
        
        # Set test data and analysis results
        self.worker.data = self.test_data
        self.worker.position_analyzer.data = self.test_data
        
        # Run the method
        self.worker.create_visualization()
        
        # Check that the visualizer methods were called correctly
        self.worker.visualizer.create_position_visualization.assert_called_once()
    
    @patch('os.makedirs')
    def test_save_outputs(self, mock_makedirs):
        """Test the save_outputs method."""
        # Mock the visualizer and report generator methods
        self.worker.visualizer.save_visualization = MagicMock()
        self.worker.report_generator.create_comprehensive_report = MagicMock(
            return_value={'excel_report': 'test.xlsx', 'pdf_report': 'test.pdf'}
        )
        
        # Mock results
        self.worker.results['visualization'] = MagicMock()
        self.worker.position_analyzer.analysis_results = {'key': 'value'}
        
        # Run the method
        self.worker.save_outputs()
        
        # Check that the methods were called correctly
        mock_makedirs.assert_called_once_with(self.test_params['output_dir'], exist_ok=True)
        self.worker.visualizer.save_visualization.assert_called_once()
        self.worker.report_generator.create_comprehensive_report.assert_called_once()
        
        # Check that the report paths were stored
        self.assertEqual(self.worker.results['reports'], 
                         {'excel_report': 'test.xlsx', 'pdf_report': 'test.pdf'})
    
    def test_extract_position_anomalies(self):
        """Test the _extract_position_anomalies method."""
        # Create test data with anomalies
        anomaly_data = self.test_data.copy()
        anomaly_data['Is_KP_Jump'] = np.zeros(100, dtype=bool)
        anomaly_data['Is_KP_Jump'][10:15] = True  # Mark some rows as anomalies
        
        # Set as the analyzer's data
        self.worker.position_analyzer.data = anomaly_data
        
        # Run the method
        result = self.worker._extract_position_anomalies()
        
        # Check the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 5)  # Should have 5 anomalies


if __name__ == '__main__':
    unittest.main()