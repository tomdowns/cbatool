# worker_utils.py

import logging
import tkinter as tk # Import tkinter for TclError check
from abc import ABC, abstractmethod
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class BaseAnalysisWorker(ABC):
    """
    Abstract base class for analysis workers running in separate threads.

    Defines the common interface and workflow (using Template Method pattern)
    for analysis tasks and handles communication back to the main UI thread
    for status and progress updates.

    Attributes:
        app: Reference to the main CableAnalysisTool UI instance.
        params: Dictionary of parameters for the analysis.
        data: DataFrame holding the loaded data for analysis.
        results: Dictionary to store final results/output paths.
        output_dir: Directory where outputs should be saved.
        success: Flag indicating if the analysis completed without critical errors.
        error_message: Stores the error message if the worker fails.
        is_cancelled: Flag for cancellation logic (to be implemented if needed).
    """

    def __init__(self, app_instance, params: Dict[str, Any]):
        """
        Initialize the worker with application instance and parameters.

        Args:
            app_instance: Reference to the main application instance (CableAnalysisTool).
            params: Dictionary of parameters needed for the analysis.
        """
        self.app = app_instance
        self.params = params
        self.data = None
        self.results: Dict[str, Any] = {}
        self.output_dir = params.get('output_dir', '.') # Ensure default if missing

        # State flags
        self.success = False
        self.error_message = None
        self.is_cancelled = False # Basic cancellation flag

    # --- Template Method ---
    def run(self):
        """Template method defining the analysis workflow executed in a thread."""
        try:
            logger.info(f"Worker started: {self.__class__.__name__}")
            # Redirect stdout/stderr within the thread if needed
            # Note: redirector needs to be thread-safe or accessed carefully
            # For simplicity, using print which should be caught by console redirector if set globally
            print(f"--- Starting {self.__class__.__name__} ---")

            # Start progress indication
            self.app.root.after(0, self._start_progress_bar) # Schedule on main thread

            # --- Step 1: Load Data ---
            # self.set_progress(5, "Loading data...") # Set progress before action
            self.load_data()
            if self.is_cancelled: return # Check for cancellation after each step
            # self.set_progress(10, "Data loaded.") # Set progress after action

            # --- Step 2: Setup Analyzer(s) ---
            # self.set_progress(15, "Configuring analyzers...")
            self.setup_analyzer()
            if self.is_cancelled: return
            # self.set_progress(20, "Analyzers configured.")

            # --- Step 3: Run Core Analysis ---
            # self.set_progress(25, "Running analysis...")
            self.run_analysis()
            if self.is_cancelled: return
            # self.set_progress(80, "Analysis complete.") # Progress might jump after long step

            # --- Step 4: Create Visualizations ---
            # self.set_progress(85, "Creating visualizations...")
            self.create_visualization()
            if self.is_cancelled: return
            # self.set_progress(95, "Visualizations created.")

            # --- Step 5: Save Outputs (including reports) ---
            # self.set_progress(96, "Generating reports...")
            self.save_outputs()
            if self.is_cancelled: return
            # self.set_progress(100, "Outputs saved.")

            # If all steps complete without error
            self.success = True
            logger.info(f"Worker finished successfully: {self.__class__.__name__}")
            print(f"--- {self.__class__.__name__} Finished Successfully ---")
            self.update_ui_status("Analysis complete.") # Final status update

        except Exception as e:
            self.handle_exception(e) # Use the dedicated handler

        finally:
            # Ensure progress bar stops/hides even on error/cancellation
            # self.set_progress(0, f"Finished with {'errors' if self.error_message else 'cancellation' if self.is_cancelled else 'success'}.")
            self.app.root.after(0, self._stop_progress_bar) # Schedule on main thread
            # Restore stdout/stderr if redirected within the thread

    # --- Abstract Methods (must be implemented by subclasses) ---
    @abstractmethod
    def load_data(self):
        """Load data required for the analysis."""
        pass

    @abstractmethod
    def setup_analyzer(self):
        """Configure the analyzer(s) with data and parameters."""
        pass

    @abstractmethod
    def run_analysis(self):
        """Execute the core analysis logic."""
        pass

    @abstractmethod
    def create_visualization(self):
        """Generate visualization artifacts."""
        pass

    @abstractmethod
    def save_outputs(self):
        """Save all generated outputs (reports, data files, etc.)."""
        pass

    # --- Helper Methods ---
    def handle_exception(self, exception: Exception):
        """Centralized exception handling for the worker thread."""
        self.success = False
        self.error_message = str(exception)
        logger.error(f"Worker failed: {self.__class__.__name__}", exc_info=True)

        # Log to console widget as well (print should be redirected)
        import traceback
        print(f"\n--- ERROR in {self.__class__.__name__} ---")
        print(f"Error: {self.error_message}")
        print(traceback.format_exc())
        print("--- End Error Traceback ---")

        # Update UI status bar (safely via main thread)
        # Pass error message directly for clarity
        self.app.root.after(0, lambda: self.update_ui_status(f"Analysis failed: {self.error_message}"))

        # Show error dialog to user (safely via main thread)
        from tkinter import messagebox
        # Use lambda to ensure the call happens correctly in the main thread context
        self.app.root.after(0, lambda exc=exception: messagebox.showerror("Analysis Error", f"An error occurred:\n{exc}"))


    def update_ui_status(self, message: str):
        """Safely update the UI status bar from the worker thread."""
        # Assumes self.app is the CableAnalysisTool instance
        # Uses the set_status method which now calls StatusBar.set_status correctly
        if hasattr(self.app, 'set_status'):
             self.app.root.after(0, lambda msg=message: self.app.set_status(msg))


    # --- PROGRESS UPDATE METHODS ---
    def set_progress(self, value: int, message: str):
        """
        Safely update the progress bar and label in the main UI thread.

        Args:
            value: Progress percentage (0-100).
            message: Status message to display alongside progress.
        """
        # Check if UI elements exist before trying to update
        # (Check app reference first)
        if not hasattr(self, 'app'): return # Should not happen if init worked
        if hasattr(self.app, 'progress_bar') and hasattr(self.app, 'progress_label'):
            # Schedule the UI update on the main thread using lambda for safety
            def update_task():
                try: # Add inner try-except for widget safety
                    progress_widget = self.app.progress_bar
                    label_widget = self.app.progress_label

                    if progress_widget.winfo_exists() and label_widget.winfo_exists():
                         # Switch from indeterminate if needed
                         if progress_widget['mode'] == 'indeterminate':
                             progress_widget.stop()
                             progress_widget.config(mode='determinate')
                         # Update values
                         progress_widget['value'] = value
                         label_widget.config(text=f"{message} [{value}%]")
                    else:
                         logger.warning("Progress bar or label does not exist, skipping update.")
                except Exception as ui_e:
                     logger.error(f"Error updating progress UI: {ui_e}", exc_info=False)

            self.app.root.after(0, update_task)


    def _start_progress_bar(self):
        """Safely start the progress bar (indeterminate) in the main UI thread."""
        if hasattr(self, 'app') and hasattr(self.app, 'progress_bar'):
            def start_task():
                try:
                     progress_widget = self.app.progress_bar
                     if progress_widget.winfo_exists():
                         progress_widget.config(mode='indeterminate')
                         progress_widget['value'] = 0 # Reset value
                         progress_widget.start(10) # Start pulsing
                         # Update label too
                         if hasattr(self.app, 'progress_label') and self.app.progress_label.winfo_exists():
                              self.app.progress_label.config(text="Analysis starting...")
                     else:
                         logger.warning("Progress bar does not exist, cannot start.")
                except Exception as ui_e:
                     logger.error(f"Error starting progress bar UI: {ui_e}", exc_info=False)

            self.app.root.after(0, start_task)


    def _stop_progress_bar(self):
        """Safely stop/reset the progress bar in the main UI thread."""
        if hasattr(self, 'app') and hasattr(self.app, 'progress_bar'):
            def stop_task():
                try:
                    progress_widget = self.app.progress_bar
                    if progress_widget.winfo_exists():
                         progress_widget.stop()
                         progress_widget.config(mode='determinate') # Set back to determinate
                         # Decide whether to show 0% or 100% at the end
                         # progress_widget['value'] = 100 if self.success else 0
                         progress_widget['value'] = 0 # Reset to 0 generally safer
                    else:
                        logger.warning("Progress bar does not exist, cannot stop.")
                except Exception as ui_e:
                    logger.error(f"Error stopping progress bar UI: {ui_e}", exc_info=False)

            self.app.root.after(0, stop_task)