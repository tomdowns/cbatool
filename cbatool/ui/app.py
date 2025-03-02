"""
Main application UI class for CBAtool v2.0.

This module contains the CableAnalysisTool class which is the main application
class for the Cable Burial Analysis Tool GUI.
"""

import os
import sys
import logging
import threading
import platform
from tkinter import (
    Tk, Frame, Label, Entry, Button, StringVar, DoubleVar, Text, Scrollbar,
    OptionMenu, filedialog, messagebox, simpledialog, ttk, Menu, BooleanVar
)

from ..core.data_loader import DataLoader
from ..core.analyzer import Analyzer
from ..core.visualizer import Visualizer
from ..utils.file_operations import select_file, open_file
from ..utils.constants import COLORS

# Configure logging
logger = logging.getLogger(__name__)

# Get system information
SYSTEM = platform.system()  # 'Darwin' for macOS, 'Windows' for Windows, 'Linux' for Linux


class ConsoleRedirector:
    """Class for redirecting print statements to a tkinter Text widget."""
    
    def __init__(self, text_widget):
        """
        Initialize the redirector with a Text widget.
        
        Args:
            text_widget: tkinter Text widget to redirect output to.
        """
        self.text_widget = text_widget
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.buffer = ""
    
    def write(self, message):
        """
        Write a message to the Text widget and the original stdout.
        
        Args:
            message: The message to write.
        """
        # Insert message into text widget
        self.text_widget.insert("end", message)
        self.text_widget.see("end")
        
        # Also write to original stdout
        self.stdout.write(message)
        
        # Store in buffer for potential later use
        self.buffer += message
    
    def flush(self):
        """Flush the buffer and update the UI."""
        self.text_widget.update_idletasks()
        self.stdout.flush()
    
    def getvalue(self):
        """
        Get the contents of the buffer.
        
        Returns:
            str: Buffer contents.
        """
        return self.buffer


class CableAnalysisTool:
    """
    Main application class for the Cable Burial Analysis Tool.
    Provides a GUI for loading, analyzing, and visualizing cable burial data.
    """
    
    def __init__(self, root):
        """
        Initialize the application with the main window.
        
        Args:
            root: tkinter root window.
        """
        self.root = root
        root.title("Cable Burial Analysis Tool v2.0")
        root.geometry("900x700")
        
        # Center the window on screen
        window_width = 900
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Apply platform-specific styling
        self._apply_platform_styling()
        
        # Create core components
        self.data_loader = DataLoader()
        self.analyzer = Analyzer()
        self.visualizer = Visualizer()
        
        # Create variables for configuration
        self._create_variables()
        
        # Build the UI
        self._create_menu()
        self._create_widgets()
        
        # Add status bar at the bottom
        self._create_status_bar()
        
       # Initialize theme based on dark mode setting
        #self._initialize_theme()
        
        # Set initial status
        self.set_status("Ready")
        
        
    
    def _apply_platform_styling(self):
        """Apply platform-specific styling to UI elements."""
        self.style = ttk.Style()
        
        if SYSTEM == "Darwin":  # macOS
            # Use native macOS appearance
            pass
        else:
            # Use a more modern theme if available
            try:
                if 'clam' in self.style.theme_names():
                    self.style.theme_use('clam')
            except Exception as e:
                logger.warning(f"Could not apply theme: {e}")
    
    def _create_variables(self):
        """Create variables for UI configuration."""
        self.file_path = StringVar()
        self.output_dir = StringVar()
        self.target_depth = DoubleVar(value=1.5)
        self.max_depth = DoubleVar(value=3.0)
        self.depth_column = StringVar()
        self.kp_column = StringVar()
        self.position_column = StringVar()
        self.sheet_name = StringVar(value="0")  # Default to first sheet
        self.ignore_anomalies = BooleanVar(value=False)
        self.dark_mode = BooleanVar(value=False)
    
    def _create_menu(self):
        """Create application menu bar."""
        self.menu_bar = Menu(self.root)
        
        # File menu
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Data File...", command=self._browse_file)
        file_menu.add_command(label="Set Output Directory...", command=self._browse_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Create Test Data...", command=self._create_test_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Analysis menu
        analysis_menu = Menu(self.menu_bar, tearoff=0)
        analysis_menu.add_command(label="Run Analysis", command=self.run_analysis)
        analysis_menu.add_command(label="View Results", command=self._view_results)
        self.menu_bar.add_cascade(label="Analysis", menu=analysis_menu)
        
        # View menu
        view_menu = Menu(self.menu_bar, tearoff=0)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode, command=self._toggle_dark_mode)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def _create_widgets(self):
        """Create and arrange all UI widgets."""
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill="both", expand=True)
        
        # Input section - file selection, parameters
        input_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10 10 10 10")
        input_frame.pack(fill="x", pady=(0, 10))
        
        # File selection
        ttk.Label(input_frame, text="Data File:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(input_frame, text="Browse...", command=self._browse_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Settings - arranged in a grid for better layout
        ttk.Label(input_frame, text="Target Depth (m):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.target_depth, width=10).grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(input_frame, text="Max Trenching Depth (m):").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.max_depth, width=10).grid(row=2, column=1, sticky="w", pady=5)
        
        # Column selectors (will be populated when file is loaded)
        ttk.Label(input_frame, text="Sheet Name:").grid(row=3, column=0, sticky="w", pady=5)
        self.sheet_menu = ttk.Combobox(input_frame, textvariable=self.sheet_name, state="readonly", width=15)
        self.sheet_menu.grid(row=3, column=1, sticky="w", pady=5)
        
        ttk.Label(input_frame, text="Depth Column:").grid(row=4, column=0, sticky="w", pady=5)
        self.depth_menu = ttk.Combobox(input_frame, textvariable=self.depth_column, state="readonly", width=15)
        self.depth_menu.grid(row=4, column=1, sticky="w", pady=5)
        
        ttk.Label(input_frame, text="KP Column:").grid(row=5, column=0, sticky="w", pady=5)
        self.kp_menu = ttk.Combobox(input_frame, textvariable=self.kp_column, state="readonly", width=15)
        self.kp_menu.grid(row=5, column=1, sticky="w", pady=5)
        
        ttk.Label(input_frame, text="Position Column:").grid(row=6, column=0, sticky="w", pady=5)
        self.position_menu = ttk.Combobox(input_frame, textvariable=self.position_column, state="readonly", width=15)
        self.position_menu.grid(row=6, column=1, sticky="w", pady=5)
        
        ttk.Label(input_frame, text="Ignore Anomalies:").grid(row=7, column=0, sticky="w", pady=5)
        ttk.Checkbutton(input_frame, variable=self.ignore_anomalies).grid(row=7, column=1, sticky="w", pady=5)
        
        # Output directory
        ttk.Label(input_frame, text="Output Directory:").grid(row=8, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.output_dir, width=50).grid(row=8, column=1, sticky="ew", pady=5)
        ttk.Button(input_frame, text="Browse...", command=self._browse_output_dir).grid(row=8, column=2, padx=5, pady=5)
        
        # Configure grid column weights
        input_frame.columnconfigure(1, weight=1)
        
        # Console output
        console_frame = ttk.LabelFrame(main_frame, text="Analysis Log", padding="10 10 10 10")
        console_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Text widget with scrollbar for console output
        self.console = Text(console_frame, wrap="word", height=10, bg="#f0f0f0")
        self.console.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(console_frame, command=self.console.yview)
        scrollbar.pack(side="right", fill="y")
        self.console.config(yscrollcommand=scrollbar.set)
        
        # Set up console redirector
        self.redirector = ConsoleRedirector(self.console)
        
        # Button frame at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        # Analysis buttons
        ttk.Button(
            button_frame, 
            text="Run Analysis",
            command=self.run_analysis
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="View Results",
            command=self._view_results
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Create Test Data",
            command=self._create_test_data
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.destroy
        ).pack(side="right")
    
    def _create_status_bar(self):
        """Create status bar at the bottom of the window."""
        self.status_bar = ttk.Label(
            self.root, 
            text="Ready", 
            relief="sunken", 
            anchor="w", 
            padding=(5, 2)
        )
        self.status_bar.pack(side="bottom", fill="x")
    
    def set_status(self, message):
        """
        Update the status bar with a message.
        
        Args:
            message: The message to display.
        """
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def _browse_file(self):
        """Open file dialog to select data file."""
        file_path = select_file()
        if file_path:
            self.file_path.set(file_path)
            self._update_file_info(file_path)
    
    def _browse_output_dir(self):
        """Open directory dialog to select output folder."""
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if output_dir:
            self.output_dir.set(output_dir)
    
    def _update_file_info(self, file_path):
        """
        Update UI based on selected file.
        
        Args:
            file_path: Path to the selected file.
        """
        # Set status
        self.set_status(f"Loading file information: {os.path.basename(file_path)}")
        
        # Load file information
        self.data_loader.set_file_path(file_path)
        
        # Update sheet selector
        self.sheet_menu['values'] = self.data_loader.sheet_names
        if self.data_loader.sheet_names:
            self.sheet_name.set(self.data_loader.sheet_names[0])
        
        # Load data to get column information
        data = self.data_loader.load_data(sheet_name=self.sheet_name.get())
        if data is None:
            messagebox.showerror("File Error", "Could not load data from the selected file")
            self.set_status("Error loading file")
            return
        
        # Update column selectors
        columns = list(data.columns)
        
        # Update depth column selector
        self.depth_menu['values'] = columns
        suggested_depth = self.data_loader.column_info.get('suggested_depth_column', None)
        if suggested_depth:
            self.depth_column.set(suggested_depth)
        elif columns:
            self.depth_column.set(columns[0])
        
        # Update KP column selector
        self.kp_menu['values'] = [""] + columns
        suggested_kp = self.data_loader.column_info.get('suggested_kp_column', None)
        if suggested_kp:
            self.kp_column.set(suggested_kp)
        
        # Update position column selector
        self.position_menu['values'] = [""] + columns
        suggested_position = self.data_loader.column_info.get('suggested_position_column', None)
        if suggested_position:
            self.position_column.set(suggested_position)
        
        # Set default output directory to same as input file
        if not self.output_dir.get():
            self.output_dir.set(os.path.dirname(file_path))
        
        # Print summary to console
        print(f"File loaded: {file_path}")
        print(f"Number of rows: {len(data)}")
        print(f"Number of columns: {len(columns)}")
        print(f"Available columns: {', '.join(columns)}")
        
        # Set status
        self.set_status(f"Loaded file: {os.path.basename(file_path)}")
    
    def _create_test_data(self):
        """Create test data file with simulated cable burial measurements."""
        # Get parameters from user
        cable_length = simpledialog.askinteger(
            "Cable Length",
            "Enter cable length in meters:",
            parent=self.root,
            minvalue=100,
            maxvalue=100000,
            initialvalue=1000
        )
        
        if cable_length is None:
            return
            
        target_depth = simpledialog.askfloat(
            "Target Depth",
            "Enter target burial depth in meters:",
            parent=self.root,
            minvalue=0.1,
            maxvalue=5.0,
            initialvalue=1.5
        )
        
        if target_depth is None:
            return
        
        # Get output file location
        output_file = filedialog.asksaveasfilename(
            title="Save Test Data",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not output_file:
            return
        
        # Clear console
        self.console.delete(1.0, "end")
        
        # Create test data
        self.set_status("Creating test data...")
        
        # Redirect stdout to console
        original_stdout = sys.stdout
        sys.stdout = self.redirector
        
        try:
            success = self.data_loader.create_test_data(
                output_file=output_file,
                cable_length=cable_length,
                target_depth=target_depth
            )
            
            if success:
                print(f"Test data created successfully.")
                print(f"File: {output_file}")
                print(f"Cable Length: {cable_length} meters")
                print(f"Target Depth: {target_depth} meters")
                
                # Ask if user wants to analyze this file
                if messagebox.askyesno(
                    "Test Data Created",
                    "Test data file created successfully. Do you want to analyze it now?"
                ):
                    self.file_path.set(output_file)
                    self._update_file_info(output_file)
                    self.target_depth.set(target_depth)
                    
                self.set_status("Test data created")
            else:
                messagebox.showerror("Error", "Failed to create test data")
                self.set_status("Error creating test data")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create test data: {str(e)}")
            self.set_status("Error creating test data")
        finally:
            sys.stdout = original_stdout
    
    def _toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        if self.dark_mode.get():
            # Dark mode - ONLY modify the console text widget
            if hasattr(self, 'console'):
                self.console.config(bg="#1e1e1e", fg="#e0e0e0")
            self.set_status("Dark mode enabled")
        else:
            # Light mode
            if hasattr(self, 'console'):
                self.console.config(bg="#f0f0f0", fg="#000000")
            self.set_status("Light mode disabled")
            
    def _initialize_theme(self):
        """Initialize theme based on current dark mode setting."""
        # Apply the current theme based on dark mode setting
        if hasattr(self, 'console'):
            self._toggle_dark_mode()
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Cable Burial Analysis Tool",
            "Cable Burial Analysis Tool v2.0\n\n"
            "A tool for analyzing cable burial depth data.\n\n"
            "Author: Thomas Downs\n"
            "Created: March 2025"
        )
    
    def _show_documentation(self):
        """Show documentation."""
        messagebox.showinfo(
            "Documentation",
            "Documentation is available in the README.md file.\n\n"
            "For more information, visit the project website."
        )
    
    def run_analysis(self):
        """Run analysis on the loaded data."""
        # Validate input parameters
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a file first.")
            return
        
        if not self.depth_column.get():
            messagebox.showerror("Error", "Please select a depth column.")
            return
        
        if not self.output_dir.get():
            # Prompt for output directory
            output_dir = filedialog.askdirectory(
                title="Select Output Directory for Analysis Results",
                initialdir=os.path.dirname(self.file_path.get())
            )
            
            if not output_dir:
                return
            
            self.output_dir.set(output_dir)
        
        # Clear console
        self.console.delete(1.0, "end")
        
        # Update status
        self.set_status("Running analysis...")
        
        # Redirect stdout to console
        original_stdout = sys.stdout
        sys.stdout = self.redirector
        
        # Run analysis in a separate thread to keep UI responsive
        self._run_analysis_thread()
    
    def _run_analysis_thread(self):
        """Run analysis in a background thread."""
        # Create and start thread
        analysis_thread = threading.Thread(target=self._analysis_worker)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def _analysis_worker(self):
        """Worker function for background analysis."""
        try:
            # 1. Load the data
            print("Loading data...")
            data = self.data_loader.load_data(sheet_name=self.sheet_name.get())
            
            if data is None or data.empty:
                messagebox.showerror("Error", "Could not load data from the selected file.")
                self.set_status("Analysis failed")
                return
            
            # 2. Set up analyzer
            print("Setting up analysis...")
            self.analyzer.set_data(data)
            self.analyzer.set_columns(
                depth_column=self.depth_column.get(),
                kp_column=self.kp_column.get() if self.kp_column.get() else None,
                position_column=self.position_column.get() if self.position_column.get() else None
            )
            self.analyzer.set_target_depth(self.target_depth.get())
            
            # 3. Run analysis
            print("Running analysis...")
            success = self.analyzer.analyze_data(
                max_depth=self.max_depth.get(),
                ignore_anomalies=self.ignore_anomalies.get()
            )
            
            if not success:
                messagebox.showerror("Analysis Error", "Analysis failed.")
                self.set_status("Analysis failed")
                return
            
            # 4. Set up visualizer
            print("Creating visualization...")
            self.visualizer.set_data(
                data=self.analyzer.data,
                problem_sections=self.analyzer.analysis_results.get('problem_sections', None)
            )
            self.visualizer.set_columns(
                depth_column=self.depth_column.get(),
                kp_column=self.kp_column.get() if self.kp_column.get() else None,
                position_column=self.position_column.get() if self.position_column.get() else None
            )
            self.visualizer.set_target_depth(self.target_depth.get())
            
            # 5. Create visualization
            fig = self.visualizer.create_visualization(
                include_anomalies=True,
                segmented=(len(data) > 5000)  # Use segmented view for large datasets
            )
            
            if fig is None:
                messagebox.showerror("Visualization Error", "Failed to create visualization.")
                self.set_status("Visualization failed")
                return
            
            # 6. Save outputs
            output_dir = self.output_dir.get()
            os.makedirs(output_dir, exist_ok=True)
            
            # Visualization
            viz_file = os.path.join(output_dir, "cable_burial_analysis.html")
            self.visualizer.save_visualization(viz_file)
            print(f"Interactive visualization saved to: {viz_file}")
            
            # Analysis summary
            summary = self.analyzer.get_analysis_summary()
            print("\nAnalysis Summary:")
            print(f"Total data points: {summary.get('data_points', 0)}")
            print(f"Target depth: {summary.get('target_depth', 0.0)}m")
            print(f"Compliance: {summary.get('compliance_percentage', 0.0):.2f}%")
            
            if 'problem_section_count' in summary:
                print(f"Problem sections: {summary.get('problem_section_count', 0)}")
                print(f"Total problem length: {summary.get('total_problem_length', 0.0):.1f}m")
            
            if 'anomaly_count' in summary:
                print(f"Anomalies detected: {summary.get('anomaly_count', 0)}")
            
            # 7. Save Excel reports
            problem_sections = self.analyzer.analysis_results.get('problem_sections', None)
            if problem_sections is not None and not problem_sections.empty:
                sections_file = os.path.join(output_dir, "problem_sections_report.xlsx")
                problem_sections.to_excel(sections_file, index=False)
                print(f"Problem sections report saved to: {sections_file}")
            
            anomalies = self.analyzer.analysis_results.get('anomalies', None)
            if anomalies is not None and not anomalies.empty:
                anomaly_file = os.path.join(output_dir, "anomaly_report.xlsx")
                anomalies.to_excel(anomaly_file, index=False)
                print(f"Anomaly report saved to: {anomaly_file}")
            
            # 8. Update UI
            print("\nAnalysis completed successfully.")
            self.set_status("Analysis complete")
            
            # Ask to view results
            if messagebox.askyesno("Analysis Complete", 
                                 "Analysis finished successfully. Open visualization?"):
                self.visualizer.open_visualization(viz_file)
            
        except Exception as e:
            import traceback
            print(f"Error during analysis: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("Analysis Error", f"An error occurred: {str(e)}")
            self.set_status("Analysis failed")
    
    def _view_results(self):
        """View analysis results."""
        # Check if analysis has been run
        if not hasattr(self.analyzer, 'analysis_results') or not self.analyzer.analysis_results:
            messagebox.showinfo("No Results", "Please run analysis first.")
            return
        
        # Check if output directory exists
        output_dir = self.output_dir.get()
        if not os.path.exists(output_dir):
            messagebox.showerror("Error", "Output directory not found.")
            return
        
        # Check if visualization file exists
        viz_file = os.path.join(output_dir, "cable_burial_analysis.html")
        if not os.path.exists(viz_file):
            messagebox.showerror("Error", "Visualization file not found.")
            return
        
        # Open visualization
        self.visualizer.open_visualization(viz_file)
