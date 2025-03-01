"""
Custom dialog boxes for CBAtool v2.0.

This module contains custom dialog boxes used in the Cable Burial Analysis Tool GUI.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import logging
from typing import Optional, Dict, Any, List, Tuple, Callable

# Configure logging
logger = logging.getLogger(__name__)


class ProgressDialog(tk.Toplevel):
    """
    A dialog box showing a progress bar for long-running operations.
    
    Attributes:
        progress_var: Variable controlling the progress bar.
        status_var: Variable containing the status message.
    """
    
    def __init__(self, parent, title="Processing...", message="Please wait", **kwargs):
        """
        Initialize a ProgressDialog.
        
        Args:
            parent: The parent window.
            title: Dialog title.
            message: Initial message to display.
            **kwargs: Additional keyword arguments for Toplevel.
        """
        super().__init__(parent, **kwargs)
        self.title(title)
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        window_width = 300
        window_height = 100
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create variables
        self.status_var = tk.StringVar(value=message)
        self.progress_var = tk.DoubleVar(value=0)
        self.is_canceled = False
        
        # Create widgets
        ttk.Label(self, textvariable=self.status_var).pack(pady=10)
        self.progress = ttk.Progressbar(
            self, 
            variable=self.progress_var,
            mode="determinate",
            length=250
        )
        self.progress.pack(pady=5)
        
        # Add cancel button
        self.cancel_button = ttk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=5)
        
        # Disable close button
        self.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def update_progress(self, value, message=None):
        """
        Update the progress bar and optionally the message.
        
        Args:
            value: Progress value (0-100).
            message: Optional new status message.
        """
        self.progress_var.set(value)
        if message:
            self.status_var.set(message)
        self.update_idletasks()
    
    def set_indeterminate(self):
        """Switch to indeterminate mode for unknown progress."""
        self.progress.config(mode="indeterminate")
        self.progress.start(10)
    
    def cancel(self):
        """Handle cancellation."""
        self.is_canceled = True
        self.status_var.set("Canceling...")
        self.cancel_button.config(state="disabled")
    
    def close(self):
        """Close the dialog."""
        self.grab_release()
        self.destroy()


class DataSelectionDialog(tk.Toplevel):
    """
    A dialog for selecting data columns and configuration.
    
    Attributes:
        result: Dictionary containing selected values.
    """
    
    def __init__(self, parent, columns, suggested_columns=None, **kwargs):
        """
        Initialize a DataSelectionDialog.
        
        Args:
            parent: The parent window.
            columns: List of available column names.
            suggested_columns: Dictionary with suggested column names.
            **kwargs: Additional keyword arguments for Toplevel.
        """
        super().__init__(parent, **kwargs)
        self.title("Select Data Columns")
        
        # Initialize variables
        self.columns = columns
        self.suggested = suggested_columns or {}
        self.result = {}
        
        # Create variables
        self.depth_column = tk.StringVar()
        self.kp_column = tk.StringVar()
        self.position_column = tk.StringVar()
        self.target_depth = tk.DoubleVar(value=1.5)
        self.max_depth = tk.DoubleVar(value=3.0)
        
        # Set suggested values if available
        if 'suggested_depth_column' in self.suggested:
            self.depth_column.set(self.suggested['suggested_depth_column'])
        
        if 'suggested_kp_column' in self.suggested:
            self.kp_column.set(self.suggested['suggested_kp_column'])
            
        if 'suggested_position_column' in self.suggested:
            self.position_column.set(self.suggested['suggested_position_column'])
        
        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill="both", expand=True)
        
        # Column selection frame
        column_frame = ttk.LabelFrame(main_frame, text="Column Selection", padding="5 5 5 5")
        column_frame.pack(fill="x", expand=True, pady=5)
        
        # Depth column
        ttk.Label(column_frame, text="Depth Column:").grid(row=0, column=0, sticky="w", pady=5)
        depth_menu = ttk.Combobox(
            column_frame, 
            textvariable=self.depth_column, 
            values=columns,
            state="readonly",
            width=20
        )
        depth_menu.grid(row=0, column=1, sticky="ew", pady=5)
        
        # KP column
        ttk.Label(column_frame, text="KP Column:").grid(row=1, column=0, sticky="w", pady=5)
        kp_menu = ttk.Combobox(
            column_frame, 
            textvariable=self.kp_column, 
            values=[""] + columns,
            state="readonly",
            width=20
        )
        kp_menu.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Position column
        ttk.Label(column_frame, text="Position Column:").grid(row=2, column=0, sticky="w", pady=5)
        position_menu = ttk.Combobox(
            column_frame, 
            textvariable=self.position_column, 
            values=[""] + columns,
            state="readonly",
            width=20
        )
        position_menu.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Parameters frame
        param_frame = ttk.LabelFrame(main_frame, text="Analysis Parameters", padding="5 5 5 5")
        param_frame.pack(fill="x", expand=True, pady=5)
        
        # Target depth
        ttk.Label(param_frame, text="Target Depth (m):").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.target_depth, width=10).grid(row=0, column=1, sticky="w", pady=5)
        
        # Max depth
        ttk.Label(param_frame, text="Max Depth (m):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.max_depth, width=10).grid(row=1, column=1, sticky="w", pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        # OK and Cancel buttons
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="right", padx=5)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Wait for dialog to close
        parent.wait_window(self)
    
    def on_ok(self):
        """Handle OK button click."""
        # Validate input
        if not self.depth_column.get():
            messagebox.showerror("Error", "Please select a depth column.")
            return
        
        # Set result
        self.result = {
            'depth_column': self.depth_column.get(),
            'kp_column': self.kp_column.get(),
            'position_column': self.position_column.get(),
            'target_depth': self.target_depth.get(),
            'max_depth': self.max_depth.get()
        }
        
        # Close dialog
        self.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click."""
        self.result = None
        self.destroy()


class SettingsDialog(tk.Toplevel):
    """
    A dialog for configuring application settings.
    
    Attributes:
        result: Dictionary containing the settings.
    """
    
    def __init__(self, parent, current_settings=None, **kwargs):
        """
        Initialize a SettingsDialog.
        
        Args:
            parent: The parent window.
            current_settings: Dictionary with current settings.
            **kwargs: Additional keyword arguments for Toplevel.
        """
        super().__init__(parent, **kwargs)
        self.title("Settings")
        self.resizable(False, False)
        
        # Initialize variables
        self.settings = current_settings or {}
        self.result = None
        
        # Create variables
        self.dark_mode = tk.BooleanVar(value=self.settings.get('dark_mode', False))
        self.ignore_anomalies = tk.BooleanVar(value=self.settings.get('ignore_anomalies', False))
        self.use_segmented_viz = tk.BooleanVar(value=self.settings.get('use_segmented_viz', True))
        self.auto_open_viz = tk.BooleanVar(value=self.settings.get('auto_open_viz', True))
        
        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill="both", expand=True)
        
        # Appearance settings
        appearance_frame = ttk.LabelFrame(main_frame, text="Appearance", padding="5 5 5 5")
        appearance_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Checkbutton(
            appearance_frame, 
            text="Dark Mode", 
            variable=self.dark_mode
        ).pack(anchor="w", pady=2)
        
        # Analysis settings
        analysis_frame = ttk.LabelFrame(main_frame, text="Analysis", padding="5 5 5 5")
        analysis_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Checkbutton(
            analysis_frame, 
            text="Ignore Anomalies in Compliance Analysis", 
            variable=self.ignore_anomalies
        ).pack(anchor="w", pady=2)
        
        # Visualization settings
        viz_frame = ttk.LabelFrame(main_frame, text="Visualization", padding="5 5 5 5")
        viz_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Checkbutton(
            viz_frame, 
            text="Use Segmented View for Large Datasets", 
            variable=self.use_segmented_viz
        ).pack(anchor="w", pady=2)
        
        ttk.Checkbutton(
            viz_frame, 
            text="Automatically Open Visualization After Analysis", 
            variable=self.auto_open_viz
        ).pack(anchor="w", pady=2)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        # OK and Cancel buttons
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="right", padx=5)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Wait for dialog to close
        parent.wait_window(self)
    
    def on_ok(self):
        """Handle OK button click."""
        self.result = {
            'dark_mode': self.dark_mode.get(),
            'ignore_anomalies': self.ignore_anomalies.get(),
            'use_segmented_viz': self.use_segmented_viz.get(),
            'auto_open_viz': self.auto_open_viz.get()
        }
        self.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click."""
        self.result = None
        self.destroy()


def get_test_data_parameters(parent):
    """
    Show a dialog to get parameters for creating test data.
    
    Args:
        parent: The parent window.
    
    Returns:
        Dictionary with parameters or None if canceled.
    """
    # Create dialog frame
    dialog = tk.Toplevel(parent)
    dialog.title("Create Test Data")
    dialog.resizable(False, False)
    
    # Make dialog modal
    dialog.transient(parent)
    dialog.grab_set()
    
    # Create variables
    cable_length = tk.IntVar(value=1000)
    target_depth = tk.DoubleVar(value=1.5)
    result = {'canceled': True}
    
    def on_ok():
        result['canceled'] = False
        result['cable_length'] = cable_length.get()
        result['target_depth'] = target_depth.get()
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    # Create main frame with padding
    main_frame = ttk.Frame(dialog, padding="10 10 10 10")
    main_frame.pack(fill="both", expand=True)
    
    # Parameter entries
    ttk.Label(main_frame, text="Cable Length (m):").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(main_frame, textvariable=cable_length, width=10).grid(row=0, column=1, sticky="w", pady=5)
    
    ttk.Label(main_frame, text="Target Depth (m):").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(main_frame, textvariable=target_depth, width=10).grid(row=1, column=1, sticky="w", pady=5)
    
    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=2, column=0, columnspan=2, pady=10)
    
    # OK and Cancel buttons
    ttk.Button(button_frame, text="OK", command=on_ok).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", padx=5)
    
    # Wait for dialog to close
    parent.wait_window(dialog)
    
    return None if result['canceled'] else {
        'cable_length': result['cable_length'],
        'target_depth': result['target_depth']
    }