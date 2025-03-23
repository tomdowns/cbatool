#!/usr/bin/env python
"""
Test runner for CBAtool worker classes.

This script runs the comprehensive test suite for CBAtool worker classes,
generating a coverage report to identify areas that need additional testing.
"""

import os
import sys
import unittest
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import coverage for reporting
try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    logger.warning("Coverage module not available. No coverage report will be generated.")
    COVERAGE_AVAILABLE = False

def run_tests_with_coverage(test_dir=None, report_dir='coverage_reports'):
    """
    Run tests with coverage reporting.
    
    Args:
        test_dir: Directory containing test files
        report_dir: Directory to save coverage reports
    
    Returns:
        tuple: (success, test_results)
    """
    if COVERAGE_AVAILABLE:
        # Create coverage object
        cov = coverage.Coverage(
            source=['cbatool.utils', 'cbatool.core'],
            omit=['*/__init__.py', '*/test_*.py']
        )
        
        # Start measuring coverage
        cov.start()
        
    # Discover and run tests
    if test_dir:
        suite = unittest.defaultTestLoader.discover(test_dir, pattern="test_*.py")
    else:
        # Default to the directory of this script
        suite = unittest.defaultTestLoader.discover(
            os.path.dirname(os.path.abspath(__file__)), 
            pattern="test_*.py"
        )
    
    # Run the test suite
    logger.info("Starting test execution...")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    if COVERAGE_AVAILABLE:
        # Stop coverage measurement
        cov.stop()
        
        # Create report directory if needed
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # HTML report
        html_report_path = os.path.join(report_dir, f'coverage_report_{timestamp}.html')
        cov.html_report(directory=os.path.join(report_dir, f'html_{timestamp}'))
        
        # XML report for CI integration
        xml_report_path = os.path.join(report_dir, f'coverage_report_{timestamp}.xml')
        cov.xml_report(outfile=xml_report_path)
        
        # Terminal report
        logger.info("Coverage Report:")
        percentage = cov.report()
        logger.info(f"Total coverage: {percentage:.2f}%")
        
        # Log report locations
        logger.info(f"HTML coverage report saved to: {os.path.abspath(os.path.join(report_dir, f'html_{timestamp}'))}")
        logger.info(f"XML coverage report saved to: {os.path.abspath(xml_report_path)}")
    
    # Log test results
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    # Return True if all tests passed
    success = len(result.errors) == 0 and len(result.failures) == 0
    
    return success, result

def run_specific_test_class(test_class_name):
    """
    Run a specific test class.
    
    Args:
        test_class_name: Name of the test class to run
        
    Returns:
        bool: True if tests passed
    """
    # Import the test module
    from test_worker_classes import TestBaseAnalysisWorker, TestDepthAnalysisWorker, TestPositionAnalysisWorker
    
    # Map of available test classes
    test_classes = {
        'TestBaseAnalysisWorker': TestBaseAnalysisWorker,
        'TestDepthAnalysisWorker': TestDepthAnalysisWorker,
        'TestPositionAnalysisWorker': TestPositionAnalysisWorker
    }
    
    if test_class_name not in test_classes:
        logger.error(f"Test class '{test_class_name}' not found.")
        logger.info(f"Available test classes: {', '.join(test_classes.keys())}")
        return False
    
    # Create test suite for the specified class
    suite = unittest.TestLoader().loadTestsFromTestCase(test_classes[test_class_name])
    
    # Run the test suite
    logger.info(f"Running tests for {test_class_name}...")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return True if all tests passed
    return len(result.errors) == 0 and len(result.failures) == 0

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for CBAtool.')
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage reporting'
    )
    parser.add_argument(
        '--test-class',
        help='Run tests for a specific test class'
    )
    parser.add_argument(
        '--report-dir',
        default='coverage_reports',
        help='Directory to save coverage reports'
    )
    args = parser.parse_args()
    
    if args.test_class:
        # Run specific test class
        success = run_specific_test_class(args.test_class)
    elif args.coverage:
        # Run all tests with coverage
        success, _ = run_tests_with_coverage(report_dir=args.report_dir)
    else:
        # Run all tests without coverage
        suite = unittest.defaultTestLoader.discover(
            os.path.dirname(os.path.abspath(__file__)),
            pattern="test_*.py"
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        success = len(result.errors) == 0 and len(result.failures) == 0
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()