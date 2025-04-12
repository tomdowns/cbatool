# -*- coding: utf-8 -*-
"""
Main application UI class for CBAtool v2.0.

This module contains the CableAnalysisTool class which is the main application
class for the Cable Burial Analysis Tool GUI, now focused on a unified
complete analysis workflow.
"""

import logging
import os
import subprocess
import platform
import sys
import threading
import sv_ttk
import tkinter as tk
from tkinter import (BooleanVar, DoubleVar, Menu, Scrollbar, StringVar, Text,
                     filedialog, messagebox, simpledialog, ttk)

# Assuming these imports are correct based on the project structure
from ..core.data_loader import DataLoader
from ..core.visualizer import Visualizer
from ..ui.dialogs import ConfigurationDialog  # Removed unused dialog imports
from ..ui.widgets import (ConsoleWidget, CreateToolTip, StatusBar,
                          TabContainer)
from ..utils.cable_registry import CableRegistry
from ..utils.config_manager import (DEFAULT_CONFIG, get_available_configurations,
                                    get_config_directory, load_configuration,
                                    save_configuration)
from ..utils.file_operations import select_file # Keep if used elsewhere, potentially only _browse_file uses filedialog
# Only import the worker we need now
from ..utils.complete_analysis_worker import CompleteAnalysisWorker


# Configure logging
logger = logging.getLogger(__name__)

# Get system information
SYSTEM = platform.system()


class CableAnalysisTool:
    """
    Main application class for the Cable Burial Analysis Tool.

    Provides a GUI for loading data, configuring parameters, running a
    complete (depth and position) analysis, and viewing results.
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the application with the main window.

        Args:
            root: The main tkinter root window.
        """
        self.root = root
        root.title("Cable Burial Analysis Tool v2.0")
        root.geometry("900x700")

        self._center_window(900, 700)
        self.style =ttk.Style()
        
        # --- Core Components ---
        self.data_loader = DataLoader()
        self.visualizer = Visualizer()
        # Analyzers are instantiated within the worker now

        # --- UI Variables ---
        self._create_variables()
        self.current_config = DEFAULT_CONFIG.copy()

        # --- Build UI ---
        self._create_menu()
        self._create_widgets()
        self._create_status_bar()

        self.set_status("Ready")

    def _center_window(self, width: int, height: int):
        """Centers the main window on the screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_coord = (screen_width - width) // 2
        y_coord = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x_coord}+{y_coord}")

    
    def _create_variables(self):
        """Create tkinter variables for UI state and parameters."""
        self.file_path = StringVar()
        self.output_dir = StringVar()
        self.sheet_name = StringVar(value="0")  # Default to first sheet
        self.cable_id = StringVar()

        # Depth Analysis Params
        self.target_depth = DoubleVar(value=DEFAULT_CONFIG["depthAnalysis"]["targetDepth"])
        self.max_depth = DoubleVar(value=DEFAULT_CONFIG["depthAnalysis"]["maxDepth"])
        self.depth_column = StringVar()
        self.ignore_anomalies = BooleanVar(value=DEFAULT_CONFIG["depthAnalysis"]["ignoreAnomalies"])

        # Position Analysis Params
        self.kp_column = StringVar()
        self.position_column = StringVar() # Legacy? Or still used?
        self.lat_column = StringVar()
        self.lon_column = StringVar()
        self.easting_column = StringVar()
        self.northing_column = StringVar()
        # Note: Thresholds are loaded from config, not direct UI vars anymore

    def _create_menu(self):
        """Create the main application menu bar."""
        self.menu_bar = Menu(self.root)

        # --- File Menu ---
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Data File...", command=self._browse_file)
        file_menu.add_command(label="Set Output Directory...", command=self._browse_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Create Test Data...", command=self._create_test_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit) # Use quit for better exit handling
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # --- Configuration Menu ---
        config_menu = Menu(self.menu_bar, tearoff=0)
        config_menu.add_command(label="Load Configuration...", command=self._load_configuration)
        config_menu.add_command(label="Save Configuration...", command=self._save_configuration)
        config_menu.add_command(label="Manage Configurations...", command=self._manage_configurations)
        config_menu.add_separator()
        config_menu.add_command(label="Reset to Default", command=self._reset_to_default)
        config_menu.add_separator()
        config_menu.add_command(label="Open Configurations Folder", command=self._show_config_directory)
        self.menu_bar.add_cascade(label="Configuration", menu=config_menu)

        # --- Analysis Menu (Simplified) ---
        analysis_menu = Menu(self.menu_bar, tearoff=0)
        analysis_menu.add_command(label="Run Analysis", command=self._trigger_analysis)
        self.menu_bar.add_cascade(label="Analysis", menu=analysis_menu)

        # --- View Menu ---
        view_menu = Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="View Latest Results", command=self._view_results)
        self.menu_bar.add_cascade(label="View", menu=view_menu)

        # --- Help Menu ---
        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menu_bar)

    def _create_widgets(self):
        """Create and arrange the main UI widgets (tabs, console)."""
        # Main content frame
        main_frame = ttk.Frame(self.root, padding="10 10 10 10") # Reduced padding slightly
        main_frame.pack(fill="both", expand=True)

        # Tab Container
        self.tab_container = TabContainer(main_frame)
        self.tab_container.pack(fill="both", expand=True, pady=(0, 10)) # Add padding below tabs

        # Create Tabs
        config_tab = self.tab_container.add_tab("config", "Configuration")
        self._create_config_tab_content(config_tab)

        analysis_tab = self.tab_container.add_tab("analysis", "Analysis")
        self._create_analysis_tab_content(analysis_tab)

        results_tab = self.tab_container.add_tab("results", "Results")
        self._create_results_tab_content(results_tab)

        # --- Console Output ---
        # Adjusted console frame packing and expansion
        console_frame = ttk.LabelFrame(main_frame, text="Analysis Log", padding="5")
        console_frame.pack(fill="both", expand=False, side="bottom", pady=(5, 0)) # Pack at bottom, don't expand vertically as much

        # Console Widget inside its frame
        self.console = ConsoleWidget(console_frame, height=8) # Set initial height
        self.console.pack(fill="both", expand=True)

        # Setup console redirection after console widget is created
        self.redirector = self.console.create_redirector()


    def _create_config_tab_content(self, tab: ttk.Frame):
        """Create contents for the Configuration tab."""
        config_frame = ttk.Frame(tab, padding="10")
        config_frame.pack(fill="both", expand=True)

        # --- Data Selection Section ---
        file_frame = ttk.LabelFrame(config_frame, text="Data Selection", padding="10")
        file_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(file_frame, text="Data File:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        ttk.Entry(file_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, sticky="ew", padx=5, pady=3)
        ttk.Button(file_frame, text="Browse...", command=self._browse_file).grid(row=0, column=2, padx=5, pady=3)

        ttk.Label(file_frame, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        ttk.Entry(file_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, sticky="ew", padx=5, pady=3)
        ttk.Button(file_frame, text="Browse...", command=self._browse_output_dir).grid(row=1, column=2, padx=5, pady=3)

        ttk.Label(file_frame, text="Sheet Name:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.sheet_menu = ttk.Combobox(file_frame, textvariable=self.sheet_name, state="readonly", width=20)
        self.sheet_menu.grid(row=2, column=1, sticky="w", padx=5, pady=3)
        file_frame.columnconfigure(1, weight=1) # Make entry expand

        # --- Cable Selector Section ---
        cable_frame_container = ttk.LabelFrame(config_frame, text="Cable Selection", padding="10")
        cable_frame_container.pack(fill="x", pady=(0, 10))
        self.cable_frame = CableRegistry.create_cable_selector(
            cable_frame_container,
            "Cable ID:",
            on_select=self._on_cable_selected,
            config=self.current_config
        )
        self.cable_frame.pack(fill="x", expand=True) # Let it expand

        # --- Analysis Parameters Section ---
        params_frame = ttk.LabelFrame(config_frame, text="Analysis Parameters", padding="10")
        params_frame.pack(fill="both", expand=True, pady=(0, 10))

        params_notebook = ttk.Notebook(params_frame)
        params_notebook.pack(fill="both", expand=True, pady=5)

        # --- Depth Analysis Tab ---
        depth_param_tab = ttk.Frame(params_notebook, padding="10")
        params_notebook.add(depth_param_tab, text="Depth")

        ttk.Label(depth_param_tab, text="Target Depth (m):").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        target_entry = ttk.Entry(depth_param_tab, textvariable=self.target_depth, width=10)
        target_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(target_entry, "Target burial depth for the cable.")

        ttk.Label(depth_param_tab, text="Max Trench Depth (m):").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        max_entry = ttk.Entry(depth_param_tab, textvariable=self.max_depth, width=10)
        max_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(max_entry, "Maximum physically possible trenching depth.")

        ttk.Label(depth_param_tab, text="Depth Column:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.depth_menu = ttk.Combobox(depth_param_tab, textvariable=self.depth_column, state="readonly", width=20)
        self.depth_menu.grid(row=2, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(self.depth_menu, "Column containing depth measurements.")

        ignore_check = ttk.Checkbutton(depth_param_tab, text="Ignore Anomalies in Compliance", variable=self.ignore_anomalies)
        ignore_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        CreateToolTip(ignore_check, "Exclude anomalous depth points from compliance calculation.")

        # --- Position Analysis Tab ---
        pos_param_tab = ttk.Frame(params_notebook, padding="10")
        params_notebook.add(pos_param_tab, text="Position")

        ttk.Label(pos_param_tab, text="KP Column:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.kp_menu = ttk.Combobox(pos_param_tab, textvariable=self.kp_column, state="readonly", width=20)
        self.kp_menu.grid(row=0, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(self.kp_menu, "Column containing KP (kilometer point) values (Required).")

        ttk.Label(pos_param_tab, text="Position Column:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.position_menu = ttk.Combobox(pos_param_tab, textvariable=self.position_column, state="readonly", width=20)
        self.position_menu.grid(row=1, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(self.position_menu, "Optional column containing generic position identifier.")

        ttk.Label(pos_param_tab, text="Latitude Column:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.lat_menu = ttk.Combobox(pos_param_tab, textvariable=self.lat_column, state="readonly", width=20)
        self.lat_menu.grid(row=2, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(self.lat_menu, "Column containing WGS84 Latitude values (Optional).")

        ttk.Label(pos_param_tab, text="Longitude Column:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.lon_menu = ttk.Combobox(pos_param_tab, textvariable=self.lon_column, state="readonly", width=20)
        self.lon_menu.grid(row=3, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(self.lon_menu, "Column containing WGS84 Longitude values (Optional).")

        ttk.Label(pos_param_tab, text="Easting Column:").grid(row=4, column=0, sticky="w", padx=5, pady=3)
        self.easting_menu = ttk.Combobox(pos_param_tab, textvariable=self.easting_column, state="readonly", width=20)
        self.easting_menu.grid(row=4, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(self.easting_menu, "Column containing Easting values (Optional).")

        ttk.Label(pos_param_tab, text="Northing Column:").grid(row=5, column=0, sticky="w", padx=5, pady=3)
        self.northing_menu = ttk.Combobox(pos_param_tab, textvariable=self.northing_column, state="readonly", width=20)
        self.northing_menu.grid(row=5, column=1, sticky="w", padx=5, pady=3)
        CreateToolTip(self.northing_menu, "Column containing Northing values (Optional).")

        ttk.Label(pos_param_tab, text="(Requires WGS84 Lat/Lon or Projected Easting/Northing)",
                  foreground="grey", font=("", 8)).grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))


    def _create_analysis_tab_content(self, tab: ttk.Frame):
        """Create contents for the Analysis tab."""
        analysis_frame = ttk.Frame(tab, padding="10")
        analysis_frame.pack(fill="both", expand=True)

        # --- Analysis Execution Section (Simplified) ---
        analysis_run_frame = ttk.LabelFrame(analysis_frame, text="Run Analysis", padding="10")
        # Make frame expand horizontally
        analysis_run_frame.pack(fill="x", pady=(0, 10))

        run_button = ttk.Button(
            analysis_run_frame,
            text="Run Complete Analysis", # Button text clarifies what it does
            command=self._trigger_analysis # Use the single trigger method
        )
        # Use pack for centering, or grid for spanning if preferred
        run_button.pack(pady=10)
        CreateToolTip(run_button, "Perform comprehensive analysis of depth and position data.")

        # --- Analysis Progress Section ---
        progress_frame = ttk.LabelFrame(analysis_frame, text="Analysis Progress", padding="10")
        progress_frame.pack(fill="x", pady=(10, 10)) # Fill horizontally

        self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate", length=100)
        self.progress_bar.pack(fill="x", expand=True, pady=5) # Make bar fill frame

        self.progress_label = ttk.Label(progress_frame, text="Ready to start analysis")
        self.progress_label.pack(pady=5)

        # --- Analysis Summary Placeholder ---
        summary_frame = ttk.LabelFrame(analysis_frame, text="Analysis Summary", padding="10")
        # Let summary expand vertically
        summary_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.summary_text = Text(summary_frame, height=10, wrap="word", state="disabled", relief="flat", bd=0) # Flat appearance
        summary_scroll = ttk.Scrollbar(summary_frame, command=self.summary_text.yview, orient="vertical")
        self.summary_text.configure(yscrollcommand=summary_scroll.set)

        summary_scroll.pack(side="right", fill="y")
        self.summary_text.pack(side="left", fill="both", expand=True)


    def _create_results_tab_content(self, tab: ttk.Frame):
        """Create contents for the Results tab."""
        results_frame = ttk.Frame(tab, padding="10")
        results_frame.pack(fill="both", expand=True)

        # --- Results Navigation/Actions ---
        nav_frame = ttk.Frame(results_frame)
        nav_frame.pack(fill="x", pady=(0, 10))

        # Simplified view - just one button to view latest results
        ttk.Button(
            nav_frame,
            text="View Latest Results Visualization",
            command=self._view_results # Keep simple _view_results call
        ).pack(side="left", padx=5)

        # Consider adding "Open Output Folder" button here?
        ttk.Button(
            nav_frame,
            text="Open Output Folder",
            command=self._open_output_folder
        ).pack(side="right", padx=5)


        # --- Results Visualization Area ---
        # Using a PanedWindow for potentially resizable sections
        # results_pane = ttk.PanedWindow(results_frame, orient=tk.VERTICAL)
        # results_pane.pack(fill="both", expand=True)

        viz_frame = ttk.LabelFrame(results_frame, text="Visualization Placeholder", padding="5")
        # results_pane.add(viz_frame, weight=3) # Give more weight to viz
        viz_frame.pack(fill="both", expand=True, pady=(0, 10)) # Pack directly for simplicity now

        self.viz_placeholder = ttk.Label(
            viz_frame,
            text="No visualization generated yet.\nRun analysis to view results.",
            anchor="center",
            justify="center",
            style="Placeholder.TLabel" # Requires defining this style
        )
        # Define placeholder style (optional, makes it look better)
        try:
            self.style.configure("Placeholder.TLabel", foreground="grey", font=("", 10))
        except tk.TclError:
             pass # Ignore if style doesn't work on platform
        self.viz_placeholder.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame for actual plot embedding (not packed initially)
        self.viz_container = ttk.Frame(viz_frame)


        # --- Results Data Summary ---
        data_frame = ttk.LabelFrame(results_frame, text="Report Summary", padding="5")
        # results_pane.add(data_frame, weight=1) # Less weight to text summary
        data_frame.pack(fill="x", pady=(0, 0), expand=False) # Pack below, don't expand vertically

        self.results_text = Text(data_frame, height=6, wrap="word", state="disabled", relief="flat", bd=0)
        data_scroll = ttk.Scrollbar(data_frame, command=self.results_text.yview, orient="vertical")
        self.results_text.configure(yscrollcommand=data_scroll.set)
        data_scroll.pack(side="right", fill="y")
        self.results_text.pack(side="left", fill="both", expand=True)

    def _create_status_bar(self):
        """Create the status bar widget at the bottom."""
        self.status_bar = StatusBar(self.root) # Use the custom StatusBar widget
        self.status_bar.pack(side="bottom", fill="x")

    def set_status(self, message: str, duration: int = 0):
        """
        Update the status bar message.

        Args:
            message: The message to display.
            duration: Time in milliseconds to display the message (0=permanent).
        """
        self.status_bar.set_status(message)
        logger.info(f"Status: {message}") # Also log status changes
        # self.root.update_idletasks() # StatusBar handles its own updates

    # --- File/Directory Handling ---

    def _browse_file(self):
        """Handle browsing for the input data file."""
        file_path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("Excel Files", "*.xlsx"),
                       ("CSV Files", "*.csv"),
                       ("All Files", "*.*")]
        )
        if file_path:
            self.file_path.set(file_path)
            # Use threading to avoid UI freeze while reading file info
            threading.Thread(target=self._update_file_info, args=(file_path,), daemon=True).start()


    def _browse_output_dir(self):
        """Handle browsing for the output directory."""
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if output_dir:
            self.output_dir.set(output_dir)
            self.set_status(f"Output directory set: {output_dir}")

    def _open_output_folder(self):
        """Opens the currently selected output folder."""
        output_dir = self.output_dir.get()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showwarning("Output Directory", "Output directory is not set or does not exist.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(output_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", output_dir], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", output_dir], check=True)
            self.set_status(f"Opened output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to open output directory '{output_dir}': {e}")
            messagebox.showerror("Error", f"Could not open output directory:\n{e}")

    def _update_file_info(self, file_path: str):
        """
        Update UI selectors based on the selected data file's contents.
        Runs in a separate thread.

        Args:
            file_path: Path to the selected data file.
        """
        try:
            self.set_status(f"Loading info: {os.path.basename(file_path)}...")
            self.data_loader.set_file_path(file_path)

            # Update sheet names
            sheet_names = self.data_loader.sheet_names
            self.sheet_menu['values'] = sheet_names
            if sheet_names:
                self.sheet_name.set(sheet_names[0])
            else:
                 self.sheet_name.set("") # Clear if no sheets

            # Load data preview to get columns (might be slow for huge files)
            # Consider loading only headers or first few rows if performance is an issue
            data_preview = self.data_loader.load_data(sheet_name=self.sheet_name.get(), nrows=5)
            if data_preview is None:
                # Schedule messagebox on main thread
                self.root.after(0, lambda: messagebox.showerror("File Error", "Could not load preview data from the selected file/sheet."))
                self.set_status("Error loading file info")
                return

            columns = [""] + list(data_preview.columns) # Add blank option

            # Update column selectors on main thread
            def update_selectors():
                self.depth_menu['values'] = columns
                self.kp_menu['values'] = columns
                self.position_menu['values'] = columns
                self.lat_menu['values'] = columns
                self.lon_menu['values'] = columns
                self.easting_menu['values'] = columns
                self.northing_menu['values'] = columns

                # Auto-select columns based on common names
                col_info = self.data_loader.column_info # Assuming this gets populated
                self.depth_column.set(col_info.get('suggested_depth_column', columns[1] if len(columns)>1 else ""))
                self.kp_column.set(col_info.get('suggested_kp_column', ""))
                self.position_column.set(col_info.get('suggested_position_column', ""))

                # Auto-select lat/lon or easting/northing
                if col_info.get('suggested_lat_column') and col_info.get('suggested_lon_column'):
                    self.lat_column.set(col_info['suggested_lat_column'])
                    self.lon_column.set(col_info['suggested_lon_column'])
                elif col_info.get('suggested_easting_column') and col_info.get('suggested_northing_column'):
                     self.easting_column.set(col_info['suggested_easting_column'])
                     self.northing_column.set(col_info['suggested_northing_column'])

                # Set default output dir if not already set
                if not self.output_dir.get() and file_path:
                    self.output_dir.set(os.path.dirname(file_path))

                # Print summary to console
                print("-" * 20)
                print(f"File Information Updated:")
                print(f"  File: {file_path}")
                print(f"  Sheet: {self.sheet_name.get()}")
                # print(f"  Rows (approx): {self.data_loader.approx_row_count}") # Requires DataLoader update
                print(f"  Columns: {list(data_preview.columns)}")
                print("-" * 20)

                self.set_status(f"File loaded: {os.path.basename(file_path)}")

            self.root.after(0, update_selectors) # Schedule UI update on main thread

        except Exception as e:
            logger.error(f"Error updating file info for '{file_path}': {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to process file information:\n{e}"))
            self.set_status("Error processing file")


    # --- Configuration Handling ---

    def _load_configuration(self):
        """Load an analysis configuration profile."""
        dialog = ConfigurationDialog(self.root, action="load")
        if dialog.result and dialog.result["action"] == "load":
            config_path = dialog.result["config_path"]
            try:
                config = load_configuration(config_path)
                self._apply_configuration(config)
                self.current_config = config # Store loaded config
                self.set_status(f"Configuration loaded: {config.get('configName', 'Unnamed')}")
                print(f"Loaded configuration from: {config_path}")
            except Exception as e:
                logger.error(f"Failed to load configuration '{config_path}': {e}", exc_info=True)
                messagebox.showerror("Load Error", f"Failed to load configuration:\n{e}")
                self.set_status("Error loading configuration")

    def _save_configuration(self):
        """Save the current analysis parameters as a configuration profile."""
        current_ui_config = self._get_current_configuration_from_ui()
        dialog = ConfigurationDialog(self.root, action="save", current_config=current_ui_config)

        if dialog.result and dialog.result["action"] == "save":
            # Update config name/desc from dialog
            current_ui_config["configName"] = dialog.result["config_name"]
            current_ui_config["description"] = dialog.result["config_description"]

            try:
                saved_path = save_configuration(current_ui_config)
                self.current_config = current_ui_config # Update stored config
                self.set_status(f"Configuration saved: {current_ui_config['configName']}")
                print(f"Configuration saved to: {saved_path}")
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}", exc_info=True)
                messagebox.showerror("Save Error", f"Failed to save configuration:\n{e}")
                self.set_status("Error saving configuration")

    def _manage_configurations(self):
        """Open dialog to rename/delete configuration profiles."""
        # Dialog handles its own logic; no action needed here after it closes
        ConfigurationDialog(self.root, action="manage")

    def _reset_to_default(self):
        """Reset UI parameters to the default configuration."""
        if messagebox.askyesno("Confirm Reset", "Reset all parameters to default values?"):
            self._apply_configuration(DEFAULT_CONFIG)
            self.current_config = DEFAULT_CONFIG.copy()
            self.set_status("Configuration reset to default")
            print("Configuration reset to default.")

    def _show_config_directory(self):
        """Open the configuration storage directory."""
        import subprocess # Keep import local as it's not always needed
        config_dir = get_config_directory()
        if os.path.isdir(config_dir):
            try:
                if platform.system() == "Windows":
                    os.startfile(config_dir)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", config_dir], check=True)
                else:
                    subprocess.run(["xdg-open", config_dir], check=True)
                self.set_status(f"Opened config directory: {config_dir}")
            except Exception as e:
                logger.error(f"Failed to open config directory '{config_dir}': {e}")
                messagebox.showerror("Error", f"Could not open config directory:\n{e}")
        else:
            logger.warning(f"Config directory not found or is not a directory: {config_dir}")
            messagebox.showwarning("Not Found", "Configuration directory does not exist yet.")

    def _get_current_configuration_from_ui(self) -> dict:
        """Gather current parameter settings from UI widgets into a config dict."""
        # Start with potentially loaded config name/desc, or defaults
        config = {
            "configName": self.current_config.get("configName", "Custom Configuration"),
            "description": self.current_config.get("description", "User-defined settings"),
            "version": self.current_config.get("version", "1.0"), # Preserve version if loaded
        }

        # --- Depth Analysis ---
        config["depthAnalysis"] = {
            "targetDepth": self.target_depth.get(),
            "maxDepth": self.max_depth.get(),
            "ignoreAnomalies": self.ignore_anomalies.get(),
            # Add other depth params if they exist as UI vars
            "minDepth": self.current_config.get("depthAnalysis", {}).get("minDepth", 0.0),
            "spikeThreshold": self.current_config.get("depthAnalysis", {}).get("spikeThreshold", 0.5),
            "windowSize": self.current_config.get("depthAnalysis", {}).get("windowSize", 5),
            "stdThreshold": self.current_config.get("depthAnalysis", {}).get("stdThreshold", 3.0),
        }

        # --- Position Analysis ---
        config["positionAnalysis"] = {
            # Add position params if they exist as UI vars
             "kpJumpThreshold": self.current_config.get("positionAnalysis", {}).get("kpJumpThreshold", 0.1),
             "kpReversalThreshold": self.current_config.get("positionAnalysis", {}).get("kpReversalThreshold", 0.0001),
             "dccThreshold": self.current_config.get("positionAnalysis", {}).get("dccThreshold", 5.0),
             "coordinateSystem": self.current_config.get("positionAnalysis", {}).get("coordinateSystem", "WGS84"),
        }

         # --- Visualization Settings ---
        config["visualization"] = self.current_config.get("visualization", {
            "useSegmented": True, "includeAnomalies": True # Defaults if not in current_config
        })

        # --- Cable Registry ---
        # Export cable registry info if the UI component exists
        if hasattr(self, 'cable_frame') and hasattr(self.cable_frame, 'registry'):
            cable_config = self.cable_frame.registry.export_to_config()
            if cable_config and 'cableIdentifiers' in cable_config:
                config['cableIdentifiers'] = cable_config['cableIdentifiers']

        return config

    def _apply_configuration(self, config: dict):
        """Apply settings from a configuration dictionary to the UI."""
        if not isinstance(config, dict):
            logger.error("Invalid configuration provided to _apply_configuration.")
            return

        # --- Depth Analysis ---
        depth_cfg = config.get("depthAnalysis", {})
        self.target_depth.set(depth_cfg.get("targetDepth", DEFAULT_CONFIG["depthAnalysis"]["targetDepth"]))
        self.max_depth.set(depth_cfg.get("maxDepth", DEFAULT_CONFIG["depthAnalysis"]["maxDepth"]))
        self.ignore_anomalies.set(depth_cfg.get("ignoreAnomalies", DEFAULT_CONFIG["depthAnalysis"]["ignoreAnomalies"]))

        # --- Position Analysis (Only non-column params) ---
        # Thresholds are now primarily handled by the config file itself,
        # but you could update UI vars if you add them later.
        pos_cfg = config.get("positionAnalysis", {})
        # Example: self.kp_jump_threshold_var.set(pos_cfg.get("kpJumpThreshold", ...))

        # --- Visualization (Only non-column params) ---
        # viz_cfg = config.get("visualization", {})
        # Example: self.use_segmented_var.set(viz_cfg.get("useSegmented", ...))

        # --- Update Cable Registry UI ---
        if hasattr(self, 'cable_frame') and hasattr(self.cable_frame, 'registry'):
            if 'cableIdentifiers' in config:
                # Create new registry instance based on loaded config
                new_registry = CableRegistry(config)
                self.cable_frame.registry = new_registry # Replace registry in UI component

                # Update the combobox values by calling the component's update method
                if hasattr(self.cable_frame, 'update_cable_list'):
                    self.cable_frame.update_cable_list()
                else: # Fallback: manually find and update combobox
                     cable_combo_values = new_registry.get_cable_ids()
                     for widget in self.cable_frame.winfo_children():
                         if isinstance(widget, ttk.Combobox) and widget.cget("textvariable") == str(self.cable_frame.cable_var):
                              widget['values'] = cable_combo_values
                              # Reset selection if current is invalid
                              if self.cable_frame.cable_var.get() not in cable_combo_values:
                                   self.cable_frame.cable_var.set("")
                              break

        # Update current_config reference
        self.current_config = config.copy() # Use a copy

        # We don't apply column settings here as they depend on the loaded data file.

    # --- Analysis Execution ---

    def _trigger_analysis(self):
        """Validate inputs and trigger the complete analysis worker thread."""
        # --- Input Validation ---
        file_path = self.file_path.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Input Error", "Please select a valid data file.")
            return

        output_dir = self.output_dir.get()
        if not output_dir:
            output_dir = filedialog.askdirectory(
                title="Select Output Directory for Analysis Results",
                initialdir=os.path.dirname(file_path)
            )
            if not output_dir:
                self.set_status("Analysis cancelled: No output directory selected.")
                return
            self.output_dir.set(output_dir)
        elif not os.path.isdir(output_dir):
             messagebox.showerror("Input Error", f"Output directory is not valid:\n{output_dir}")
             return


        depth_col = self.depth_column.get()
        if not depth_col:
            messagebox.showerror("Input Error", "Please select a Depth Column (Configuration tab).")
            return

        kp_col = self.kp_column.get()
        if not kp_col:
            messagebox.showerror("Input Error", "Please select a KP Column (Configuration tab).")
            return

        # --- Prepare Parameters ---
        # Use current_config as the base for thresholds etc.
        params = {
            'file_path': file_path,
            'output_dir': output_dir,
            'sheet_name': self.sheet_name.get(),
            'cable_id': self.cable_id.get() or None,

            # Depth params from UI / config
            'depth_column': depth_col,
            'target_depth': self.target_depth.get(),
            'max_depth': self.max_depth.get(),
            'ignore_anomalies': self.ignore_anomalies.get(),
            'depth_config': self.current_config.get('depthAnalysis', {}).copy(), # Pass full sub-config

            # Position params from UI / config
            'kp_column': kp_col,
            'position_column': self.position_column.get() or None,
            'lat_column': self.lat_column.get() or None,
            'lon_column': self.lon_column.get() or None,
            'easting_column': self.easting_column.get() or None,
            'northing_column': self.northing_column.get() or None,
            'position_config': self.current_config.get('positionAnalysis', {}).copy(), # Pass full sub-config

             # Visualization params from config
            'visualization_config': self.current_config.get('visualization', {}).copy()
        }

        # --- Execution ---
        self.console.clear()
        self.set_status("Starting complete analysis...")
        print("-" * 30)
        print("Starting Complete Analysis Run")
        print(f"Input File: {params['file_path']}")
        print(f"Output Dir: {params['output_dir']}")
        print(f"Config Used: {self.current_config.get('configName', 'Custom')}")
        print("-" * 30)


        try:
            # Create and start the worker thread
            worker = CompleteAnalysisWorker(self, params) # Pass self for UI updates
            analysis_thread = threading.Thread(target=worker.run, daemon=True)
            analysis_thread.start()
            # Optionally: Start progress bar here
            # self.progress_bar.start()
            self.set_status("Analysis running in background...")
        except Exception as e:
            logger.error("Failed to start analysis worker thread", exc_info=True)
            messagebox.showerror("Thread Error", f"Could not start analysis thread:\n{e}")
            self.set_status("Failed to start analysis")


    # --- Results Handling ---

    def _view_results(self):
        """Open visualizations for the most recently run analysis."""
        output_dir = self.output_dir.get()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showwarning("View Results", "Output directory not set or invalid. Cannot locate results.")
            return

        # Since we only run complete analysis, check for both viz files
        depth_viz = os.path.join(output_dir, "cable_burial_analysis.html")
        pos_viz = os.path.join(output_dir, "position_quality_analysis.html")
        report_excel = os.path.join(output_dir, "complete_analysis_report.xlsx") # Assuming this is the name now

        found_depth = os.path.exists(depth_viz)
        found_pos = os.path.exists(pos_viz)
        found_excel = os.path.exists(report_excel)

        if not found_depth and not found_pos and not found_excel:
             messagebox.showinfo("View Results", "No analysis results found in the output directory.")
             return

        # Simple approach: Just open the output folder
        self._open_output_folder()
        # More complex: Show dialog to choose which file to open if multiple exist.
        # For now, opening the folder is simplest.

    def _refresh_results(self):
        """ Placeholder: Refresh results displayed in the UI (if any). """
        # Currently, results are mainly external files.
        # This could be used later to update embedded summaries or plots.
        self.set_status("Results refreshed (external files).")
        print("Result refresh triggered (check output folder).")
        # Example: update summary text if results are stored internally
        # if hasattr(self,'last_analysis_summary'):
        #     self._update_results_text(self.last_analysis_summary)

    def _update_results_text(self, results: dict):
        """Update the results text widget (basic summary)."""
        if not hasattr(self, 'results_text'): return
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        summary_lines = []
        # Extract key summary points - this needs refinement based on
        # the actual structure returned by CompleteAnalysisWorker's standardized results
        if results:
             summary_lines.append(f"Analysis Type: {results.get('analysis_type', 'N/A')}")
             # Example: Add depth compliance
             depth_comp = results.get('depth_results',{}).get('compliance_metrics',{}).get('total_compliance_percentage')
             if depth_comp is not None:
                  summary_lines.append(f"Depth Compliance: {depth_comp:.2f}%")
             # Example: Add position anomalies count
             pos_anom = results.get('position_results',{}).get('anomalies',{}).get('total_count')
             if pos_anom is not None:
                  summary_lines.append(f"Position Anomalies: {pos_anom}")
        else:
             summary_lines.append("No summary data available.")

        self.results_text.insert(tk.END, "\n".join(summary_lines))
        self.results_text.config(state="disabled")

    # --- Other UI Callbacks ---

    def _on_cable_selected(self, cable_id: str):
        """Callback when a cable is selected."""
        self.cable_id.set(cable_id)
        self.set_status(f"Selected cable: {cable_id}")
        print(f"Selected cable ID: {cable_id}")
        # Potentially load cable metadata here if needed elsewhere

    def _create_test_data(self):
        """Trigger the creation of a test data file."""
        # Use simpledialog for parameters
        cable_length = simpledialog.askinteger("Cable Length", "Enter cable length (m):", parent=self.root, initialvalue=1000, minvalue=100)
        if cable_length is None: return
        target_depth = simpledialog.askfloat("Target Depth", "Enter target depth (m):", parent=self.root, initialvalue=1.5, minvalue=0.1)
        if target_depth is None: return

        output_file = filedialog.asksaveasfilename(
            title="Save Test Data File",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")]
        )
        if not output_file: return

        self.console.clear()
        self.set_status("Creating test data...")
        print("Creating test data file...")
        original_stdout = sys.stdout
        sys.stdout = self.redirector # Redirect print to console widget
        try:
            # Run in thread to avoid blocking UI
            def task():
                try:
                    success = self.data_loader.create_test_data(output_file, cable_length, target_depth)
                    if success:
                        print(f"Test data created successfully: {output_file}")
                        self.set_status("Test data created")
                        if messagebox.askyesno("Test Data Created", "Test data created. Load it now?"):
                            self.file_path.set(output_file)
                            # Need to run _update_file_info in main thread or via thread
                            self.root.after(0, lambda: threading.Thread(target=self._update_file_info, args=(output_file,), daemon=True).start())
                    else:
                        print("Failed to create test data.")
                        messagebox.showerror("Error", "Failed to create test data.")
                        self.set_status("Error creating test data")
                except Exception as e_inner:
                    logger.error("Error in test data creation thread", exc_info=True)
                    messagebox.showerror("Error", f"Failed to create test data:\n{e_inner}")
                    self.set_status("Error creating test data")
                finally:
                     sys.stdout = original_stdout # Restore stdout in thread

            threading.Thread(target=task, daemon=True).start()

        except Exception as e: # Catch error starting thread
            logger.error("Failed to start test data thread", exc_info=True)
            sys.stdout = original_stdout # Restore stdout
            messagebox.showerror("Error", f"Could not start test data creation:\n{e}")
            self.set_status("Error starting test data creation")


    def _show_about(self):
        """Display the About dialog."""
        messagebox.showinfo(
            "About Cable Burial Analysis Tool",
            "Cable Burial Analysis Tool v2.0\n\n"
            "Provides comprehensive analysis of cable burial depth and position data.\n\n"
            "Author: Thomas Downs\n"
            "(C) 2025" # Update year if needed
        )

    def _show_documentation(self):
        """Show placeholder for documentation access."""
        # Consider opening a local README.md or a web URL
        messagebox.showinfo(
            "Documentation",
            "Please refer to the README.md file included with the application "
            "or visit the project's online repository for documentation."
        )

    # --- Deprecated Methods Placeholder ---
    # Leave these commented out or remove entirely if sure they are not called
    # def _analysis_worker(self): pass
    # def _position_analysis_worker(self, ...): pass
    # def _complete_analysis_worker(self): pass
    # def run_analysis(self): pass # Keep if called by old menu item temporarily
    # def run_position_analysis(self): pass # Keep if called by old menu item temporarily
    # def _run_analysis_thread(self): pass
    # def _run_position_analysis_thread(self, ...): pass
    # def _generate_comprehensive_report(self): pass # Report generation now part of worker

# Example of how to run the application (usually in __main__.py or similar)
#if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #sv_ttk.set_theme("dark")
   # root = tk.Tk()
    #app = CableAnalysisTool(root)
    # Optionally redirect print statements for the entire app run
    # sys.stdout = app.redirector
    # sys.stderr = app.redirector # Also redirect errors if desired
    #root.mainloop()