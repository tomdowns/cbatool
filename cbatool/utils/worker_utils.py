# worker_utils.py

import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class BaseAnalysisWorker:
    """
    Base class for all analysis workers, defining the common interface.
    
    This abstract base class provides the structure for worker types,
    ensuring consistent behavior and error handling.
    """
    
    def __init__(self, app_instance, params: Dict[str, Any]):
        """
        Initialize the worker with application instance and parameters.
        
        Args:
            app_instance: Reference to the main application instance
            params: Dictionary of parameters needed for the analysis
        """
        self.app = app_instance
        self.params = params
        self.data = None
        self.results = {}
        self.output_dir = params.get('output_dir', '')
        
    def run(self):
        """
        Main execution method that runs the complete analysis pipeline.
        
        This implements the Template Method pattern, defining the skeleton
        of the algorithm while allowing subclasses to override specific steps.
        """
        try:
            # Redirect stdout to console
            import sys
            original_stdout = sys.stdout
            sys.stdout = self.app.redirector
            
            try:
                # Execute pipeline steps
                self.load_data()
                self.setup_analyzer()
                self.run_analysis()
                self.create_visualization()
                self.save_outputs()
                self.update_ui_status("Analysis complete")
            finally:
                # Restore stdout
                sys.stdout = original_stdout
                
        except Exception as e:
            self.handle_exception(e)
    
    def load_data(self):
        """Load data from the specified file."""
        raise NotImplementedError("Subclasses must implement load_data")
    
    def setup_analyzer(self):
        """Setup the analyzer with appropriate columns and parameters."""
        raise NotImplementedError("Subclasses must implement setup_analyzer")
    
    def run_analysis(self):
        """Run the analysis process."""
        raise NotImplementedError("Subclasses must implement run_analysis")
    
    def create_visualization(self):
        """Create visualization based on analysis results."""
        raise NotImplementedError("Subclasses must implement create_visualization")
    
    def save_outputs(self):
        """Save analysis outputs to files."""
        raise NotImplementedError("Subclasses must implement save_outputs")
    
    def handle_exception(self, exception):
        """Handle exceptions that occur during analysis."""
        import traceback
        print(f"Error during analysis: {str(exception)}")
        print(traceback.format_exc())
        self.app.set_status("Analysis failed")
        
        # Show error dialog to user
        from tkinter import messagebox
        messagebox.showerror("Analysis Error", f"An error occurred: {str(exception)}")
    
    def update_ui_status(self, message):
        """Update the UI status with a message."""
        self.app.set_status(message)