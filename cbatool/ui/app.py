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
import pandas as pd
from tkinter import (
	Tk, Frame, Label, Entry, Button, StringVar, DoubleVar, Text, Scrollbar,
	OptionMenu, filedialog, messagebox, simpledialog, ttk, Menu, BooleanVar,Toplevel
)
import tkinter as tk

from ..core.data_loader import DataLoader
from ..core.depth_analyzer import DepthAnalyzer
from ..core.position_analyzer import PositionAnalyzer
from ..core.visualizer import Visualizer
from ..utils.file_operations import select_file, open_file
from ..utils.report_generator import ReportGenerator
from .dialogs import DataSelectionDialog, SettingsDialog, ConfigurationDialog
from ..ui.widgets import(
	CollapsibleFrame,
	CreateToolTip,
	ConsoleWidget,
	ScrollableFrame,
	StatusBar,
	TabContainer
)
from ..utils.config_manager import (
	load_configuration,
 	save_configuration,
	get_available_configurations,
	DEFAULT_CONFIG
)
from ..utils.cable_registry import CableRegistry

# Configure logging
logger = logging.getLogger(__name__)

# Get system information
SYSTEM = platform.system()  # 'Darwin' for macOS, 'Windows' for Windows, 'Linux' for Linux

# Import worker classes
from ..utils.worker_utils import BaseAnalysisWorker
from ..utils.depth_analysis_worker import DepthAnalysisWorker
from ..utils.position_analysis_worker import PositionAnalysisWorker
from ..utils.complete_analysis_worker import CompleteAnalysisWorker


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
		self.depth_analyzer = DepthAnalyzer()
		self.position_analyzer = PositionAnalyzer()
		self.visualizer = Visualizer()
		
		
		# Create variables for configuration
		self._create_variables()
		self.current_config = DEFAULT_CONFIG.copy()
		
		# Build the UI
		self._create_menu()
		self._create_widgets()
		
		# Add status bar at the bottom
		self._create_status_bar()
		
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
		self.lat_column = StringVar()
		self.lon_column = StringVar()
		self.easting_column = StringVar() 
		self.northing_column = StringVar()
		self.sheet_name = StringVar(value="0")  # Default to first sheet
		self.ignore_anomalies = BooleanVar(value=False)
		self.cable_id = StringVar()  # Added for cable selection
	
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
		
		# Configuration menu (new)
		config_menu = Menu(self.menu_bar, tearoff=0)
		config_menu.add_command(label="Load Configuration...", command=self._load_configuration)
		config_menu.add_command(label="Save Configuration...", command=self._save_configuration)
		config_menu.add_command(label="Manage Configurations...", command=self._manage_configurations)
		config_menu.add_separator()
		config_menu.add_command(label="Reset to Default", command=self._reset_to_default)
		config_menu.add_separator()
		config_menu.add_command(label="Open Configurations Folder", command=self._show_config_directory)
		self.menu_bar.add_cascade(label="Configuration", menu=config_menu)	
  
  		# Analysis menu
		analysis_menu = Menu(self.menu_bar, tearoff=0)
		analysis_menu.add_separator()
		analysis_menu.add_command(label="Generate Comprehensive Report", command=self._generate_comprehensive_report)
		analysis_menu.add_command(label="Run Analysis", command=self.run_analysis)
		analysis_menu.add_command(label="View Results", command=self._view_results)
		self.menu_bar.add_cascade(label="Analysis", menu=analysis_menu)
		
		# View menu
		view_menu = Menu(self.menu_bar, tearoff=0)
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
		
		# Create tab container
		self.tab_container = TabContainer(main_frame)
		self.tab_container.pack(fill="both", expand=True)
		
		# Create configuration tab
		config_tab = self.tab_container.add_tab("config", "Configuration")
		self._create_config_tab_content(config_tab)
		
		# Create analysis tab
		analysis_tab = self.tab_container.add_tab("analysis", "Analysis")
		self._create_analysis_tab_content(analysis_tab)
		
		# Create results tab
		results_tab = self.tab_container.add_tab("results", "Results")
		self._create_results_tab_content(results_tab)
		
		# Create console output at the bottom
		console_frame = ttk.LabelFrame(main_frame, text="Analysis Log", padding="10 10 10 10")
		console_frame.pack(fill="both", expand=True, pady=(10, 10))
		
		# Create ConsoleWidget
		self.console = ConsoleWidget(console_frame)
		self.console.pack(fill="both", expand=True)
		
		# Set up console redirector
		self.redirector = self.console.create_redirector()
	
	def _create_config_tab_content(self, tab):
		"""Create contents for the Configuration tab."""
		# Create configuration frame with padding
		config_frame = ttk.Frame(tab, padding="10")
		config_frame.pack(fill="both", expand=True)
		
		# File selection section
		file_frame = ttk.LabelFrame(config_frame, text="Data Selection", padding="10")
		file_frame.pack(fill="x", pady=(0, 10))
		
		# File selection
		ttk.Label(file_frame, text="Data File:").grid(row=0, column=0, sticky="w", pady=5)
		ttk.Entry(file_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, sticky="ew", pady=5)
		ttk.Button(file_frame, text="Browse...", command=self._browse_file).grid(row=0, column=2, padx=5, pady=5)
		
		# Output directory
		ttk.Label(file_frame, text="Output Directory:").grid(row=1, column=0, sticky="w", pady=5)
		ttk.Entry(file_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, sticky="ew", pady=5)
		ttk.Button(file_frame, text="Browse...", command=self._browse_output_dir).grid(row=1, column=2, padx=5, pady=5)
		
		# Sheet selector
		ttk.Label(file_frame, text="Sheet Name:").grid(row=2, column=0, sticky="w", pady=5)
		self.sheet_menu = ttk.Combobox(file_frame, textvariable=self.sheet_name, state="readonly", width=15)
		self.sheet_menu.grid(row=2, column=1, sticky="w", pady=5)
		
		# Configure grid column weights
		file_frame.columnconfigure(1, weight=1)
		
		# Cable selector section
		cable_frame = ttk.LabelFrame(config_frame, text="Cable Selection", padding="10")
		cable_frame.pack(fill="x", pady=(0, 10))
		
		self.cable_frame = CableRegistry.create_cable_selector(
			cable_frame, 
			"Cable ID:", 
			on_select=self._on_cable_selected,
			config=self.current_config
		)
		self.cable_frame.pack(fill="x", pady=5)
		
		# Analysis Parameters Section
		params_frame = ttk.LabelFrame(config_frame, text="Analysis Parameters", padding="10")
		params_frame.pack(fill="both", expand=True, pady=(0, 10))
		
		# Create a notebook for parameter groups
		params_notebook = ttk.Notebook(params_frame)
		params_notebook.pack(fill="both", expand=True, pady=5)
		
		# Depth Analysis Parameters
		depth_frame = ttk.Frame(params_notebook, padding="10")
		params_notebook.add(depth_frame, text="Depth Analysis")
		
		ttk.Label(depth_frame, text="Target Depth (m):").grid(row=0, column=0, sticky="w", pady=2)
		target_entry = ttk.Entry(depth_frame, textvariable=self.target_depth, width=10)
		target_entry.grid(row=0, column=1, sticky="w", pady=2)
		CreateToolTip(target_entry, "Target burial depth for the cable")
		
		ttk.Label(depth_frame, text="Max Trenching Depth (m):").grid(row=1, column=0, sticky="w", pady=2)
		max_entry = ttk.Entry(depth_frame, textvariable=self.max_depth, width=10)
		max_entry.grid(row=1, column=1, sticky="w", pady=2)
		CreateToolTip(max_entry, "Maximum physically possible trenching depth")
		
		ttk.Label(depth_frame, text="Depth Column:").grid(row=2, column=0, sticky="w", pady=2)
		self.depth_menu = ttk.Combobox(depth_frame, textvariable=self.depth_column, state="readonly", width=15)
		self.depth_menu.grid(row=2, column=1, sticky="w", pady=2)
		CreateToolTip(self.depth_menu, "Column containing depth measurements")
		
		ignore_check = ttk.Checkbutton(depth_frame, text="Ignore Anomalies", variable=self.ignore_anomalies)
		ignore_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
		CreateToolTip(ignore_check, "Exclude anomalous points from compliance analysis")
		
		# Position Analysis Parameters
		position_frame = ttk.Frame(params_notebook, padding="10")
		params_notebook.add(position_frame, text="Position Analysis")
		
		ttk.Label(position_frame, text="KP Column:").grid(row=0, column=0, sticky="w", pady=2)
		self.kp_menu = ttk.Combobox(position_frame, textvariable=self.kp_column, state="readonly", width=15)
		self.kp_menu.grid(row=0, column=1, sticky="w", pady=2)
		CreateToolTip(self.kp_menu, "Column containing KP (kilometer point) values")
		
		ttk.Label(position_frame, text="Position Column:").grid(row=1, column=0, sticky="w", pady=2)
		self.position_menu = ttk.Combobox(position_frame, textvariable=self.position_column, state="readonly", width=15)
		self.position_menu.grid(row=1, column=1, sticky="w", pady=2)
		CreateToolTip(self.position_menu, "Column containing position values")
		
		ttk.Label(position_frame, text="Latitude Column:").grid(row=3, column=0, sticky="w", pady=2)
		self.lat_menu = ttk.Combobox(position_frame, textvariable=self.lat_column, state="readonly", width=15)
		self.lat_menu.grid(row=3, column=1, sticky="w", pady=2)
		CreateToolTip(self.lat_menu, "Column containing latitude values")
		
		ttk.Label(position_frame, text="Longitude Column:").grid(row=4, column=0, sticky="w", pady=2)
		self.lon_menu = ttk.Combobox(position_frame, textvariable=self.lon_column, state="readonly", width=15)
		self.lon_menu.grid(row=4, column=1, sticky="w", pady=2)
		CreateToolTip(self.lon_menu, "Column containing longitude values")
		
		# Easting/Northing fields
		ttk.Label(position_frame, text="Easting Column:").grid(row=5, column=0, sticky="w", pady=2)
		self.easting_menu = ttk.Combobox(position_frame, textvariable=self.easting_column, state="readonly", width=15)
		self.easting_menu.grid(row=5, column=1, sticky="w", pady=2)
		CreateToolTip(self.easting_menu, "Column containing easting values")
		
		ttk.Label(position_frame, text="Northing Column:").grid(row=6, column=0, sticky="w", pady=2)
		self.northing_menu = ttk.Combobox(position_frame, textvariable=self.northing_column, state="readonly", width=15)
		self.northing_menu.grid(row=6, column=1, sticky="w", pady=2)
		CreateToolTip(self.northing_menu, "Column containing northing values")
		
		# WGS84 coordinate system note
		ttk.Label(position_frame, text="Note: Position analysis uses WGS84 coordinate system", 
				foreground="blue", font=("", 8, "italic")).grid(
				row=7, column=0, columnspan=2, sticky="w", pady=(0, 5))

	def _create_analysis_tab_content(self, tab):
		"""Create contents for the Analysis tab."""
		# Create main frame for analysis tab
		analysis_frame = ttk.Frame(tab, padding="10")
		analysis_frame.pack(fill="both", expand=True)
		
		# Analysis type selection
		analysis_type_frame = ttk.LabelFrame(analysis_frame, text="Analysis Type", padding="10")
		analysis_type_frame.pack(fill="x", pady=(0, 10))
		
		# Create a grid of analysis buttons
		depth_button = ttk.Button(
			analysis_type_frame, 
			text="Run Depth Analysis",
			command=self.run_analysis
		)
		depth_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
		CreateToolTip(depth_button, "Analyze cable burial depth data only")
		
		position_button = ttk.Button(
			analysis_type_frame,
			text="Run Position Analysis",
			command=self.run_position_analysis
		)
		position_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
		CreateToolTip(position_button, "Analyze cable position data only")
		
		complete_button = ttk.Button(
			analysis_type_frame,
			text="Run Complete Analysis",
			command=self.run_complete_analysis
		)
		complete_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
		CreateToolTip(complete_button, "Perform comprehensive analysis of depth and position data")
		
		# Configure the grid
		for i in range(3):
			analysis_type_frame.columnconfigure(i, weight=1)
		
		# Analysis progress section
		progress_frame = ttk.LabelFrame(analysis_frame, text="Analysis Progress", padding="10")
		progress_frame.pack(fill="both", expand=True, pady=(0, 10))
		
		# Progress indicator
		self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate", length=100)
		self.progress_bar.pack(fill="x", pady=10)
		
		# Progress status
		self.progress_label = ttk.Label(progress_frame, text="Ready to start analysis")
		self.progress_label.pack(pady=5)
		
		# Analysis summary placeholder
		summary_frame = ttk.LabelFrame(analysis_frame, text="Analysis Summary", padding="10")
		summary_frame.pack(fill="both", expand=True)
		
		self.summary_text = tk.Text(summary_frame, height=10, wrap="word", state="disabled")
		summary_scroll = ttk.Scrollbar(summary_frame, command=self.summary_text.yview)
		self.summary_text.configure(yscrollcommand=summary_scroll.set)
		
		self.summary_text.pack(side="left", fill="both", expand=True)
		summary_scroll.pack(side="right", fill="y")

	def _create_results_tab_content(self, tab):
		"""Create contents for the Results tab."""
		# Create main frame for results tab
		results_frame = ttk.Frame(tab, padding="10")
		results_frame.pack(fill="both", expand=True)
		
		# Results navigation
		nav_frame = ttk.Frame(results_frame)
		nav_frame.pack(fill="x", pady=(0, 10))
		
		ttk.Button(
			nav_frame,
			text="View Depth Results",
			command=lambda: self._view_results(analysis_type="depth")
		).pack(side="left", padx=5)
		
		ttk.Button(
			nav_frame,
			text="View Position Results",
			command=lambda: self._view_results(analysis_type="position")
		).pack(side="left", padx=5)
		
		ttk.Button(
			nav_frame,
			text="Refresh Results",
			command=self._refresh_results
		).pack(side="right", padx=5)
		
		# Results visualization area
		viz_frame = ttk.LabelFrame(results_frame, text="Visualization", padding="10")
		viz_frame.pack(fill="both", expand=True, pady=(0, 10))
		
		# Placeholder for visualization
		self.viz_placeholder = ttk.Label(
			viz_frame, 
			text="No visualization available.\nRun an analysis first to see results.",
			anchor="center"
		)
		self.viz_placeholder.pack(fill="both", expand=True)
		
		# Create frame for visualization that will be populated later
		self.viz_container = ttk.Frame(viz_frame)
		# Don't pack this yet - it will replace the placeholder when visualization is available
		
		# Results data area
		data_frame = ttk.LabelFrame(results_frame, text="Data Summary", padding="10")
		data_frame.pack(fill="x", pady=(0, 10), expand=False)
		
		# Placeholder for results data
		self.results_text = tk.Text(data_frame, height=5, wrap="word", state="disabled")
		data_scroll = ttk.Scrollbar(data_frame, command=self.results_text.yview)
		self.results_text.configure(yscrollcommand=data_scroll.set)
		
		self.results_text.pack(side="left", fill="both", expand=True)
		data_scroll.pack(side="right", fill="y")
	
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

	def _load_configuration(self):
		"""Open dialog to load a configuration."""
		dialog = ConfigurationDialog(self.root, action="load")
		if dialog.result and dialog.result["action"] == "load":
			config_path = dialog.result["config_path"]
			try:
				# Load the configuration
				config = load_configuration(config_path)
				
				# Update the UI with the loaded configuration
				self._apply_configuration(config)
				
				# Update current_config
				self.current_config = config
				
				self.set_status(f"Configuration loaded: {config.get('configName', 'Unnamed')}")
			except Exception as e:
				messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
				self.set_status("Error loading configuration")

	def _save_configuration(self):
		"""Open dialog to save the current configuration."""
		# Build current configuration from UI settings
		config = self._get_current_configuration()
		
		dialog = ConfigurationDialog(self.root, action="save", current_config=config)
		if dialog.result and dialog.result["action"] == "save":
			# Update configuration name and description
			config["configName"] = dialog.result["config_name"]
			config["description"] = dialog.result["config_description"]
			
			try:
				# Save the configuration
				save_configuration(config)
				
				# Update current_config
				self.current_config = config
				
				self.set_status(f"Configuration saved: {config['configName']}")
			except Exception as e:
				messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
				self.set_status("Error saving configuration")

	def _manage_configurations(self):
		"""Open dialog to manage configurations."""
		dialog = ConfigurationDialog(self.root, action="manage")
		# No specific action needed after dialog closes

	def _reset_to_default(self):
		"""Reset configuration to default values."""
		if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset to default configuration?"):
			# Reset the configuration
			self._apply_configuration(DEFAULT_CONFIG)
			
			# Update current_config
			self.current_config = DEFAULT_CONFIG.copy()
			
			self.set_status("Configuration reset to default")

	def _show_config_directory(self):
		"""Open the configurations directory in the system file explorer."""
		from ..utils.config_manager import get_config_directory
		import platform
		import os
		import subprocess
		
		config_dir = get_config_directory()
		if os.path.exists(config_dir):
			try:
				# Use system-specific command to open folder
				if platform.system() == "Windows":
					os.startfile(config_dir)
				elif platform.system() == "Darwin":  # macOS
					subprocess.run(["open", config_dir])
				else:  # Linux
					subprocess.run(["xdg-open", config_dir])
				
				self.set_status(f"Opened configurations directory: {config_dir}")
			except Exception as e:
				messagebox.showerror("Error", f"Failed to open configurations directory: {str(e)}")
		else:
			messagebox.showerror("Error", "Configurations directory not found.")

	def _get_current_configuration(self):
		"""
		Get the current configuration from UI settings.
		
		Returns:
			dict: Current configuration dictionary.
		"""
		config = {
			"configName": self.current_config.get("configName", "My Configuration"),
			"description": self.current_config.get("description", ""),
			"version": "1.0",
			"depthAnalysis": {
				"targetDepth": self.target_depth.get(),
				"maxDepth": self.max_depth.get(),
				"minDepth": 0.0,
				"spikeThreshold": 0.5,
				"windowSize": 5,
				"stdThreshold": 3.0,
				"ignoreAnomalies": self.ignore_anomalies.get()
			},
			"positionAnalysis": {
				"kpJumpThreshold": 0.1,
				"kpReversalThreshold": 0.0001,
				"dccThreshold": 5.0,
				"coordinateSystem": "WGS84"
			},
			"visualization": {
				"useSegmented": True,
				"includeAnomalies": True
			}
		}
		
		# Add cable registry information if available
		if hasattr(self, 'cable_frame') and hasattr(self.cable_frame, 'registry'):
			# Export cable registry to config format
			cable_config = self.cable_frame.registry.export_to_config()
			if cable_config and 'cableIdentifiers' in cable_config:
				config['cableIdentifiers'] = cable_config['cableIdentifiers']
				
		return config

	def _apply_configuration(self, config):
		"""
		Apply a configuration to the UI.
		
		Args:
			config: Configuration dictionary to apply.
		"""
		# Apply depth analysis settings
		depth_config = config.get("depthAnalysis", {})
		self.target_depth.set(depth_config.get("targetDepth", 1.5))
		self.max_depth.set(depth_config.get("maxDepth", 3.0))
		self.ignore_anomalies.set(depth_config.get("ignoreAnomalies", False))
		
		# Apply position analysis settings if needed
		# ...
		
		# Apply visualization settings if needed
		# ...
		
		# Update cable selector with new configuration (if it exists)
		if hasattr(self, 'cable_frame') and hasattr(self.cable_frame, 'registry'):
			# Initialize from config if cable identifiers are provided
			if 'cableIdentifiers' in config:
				new_registry = CableRegistry(config)
				self.cable_frame.registry = new_registry
				
				# Update the combobox values
				cable_combo_values = new_registry.get_cable_ids()
				
				# Find the combobox in the frame's children
				for child in self.cable_frame.winfo_children():
					if isinstance(child, ttk.Combobox):
						child['values'] = cable_combo_values
						break
		
		# Note: We don't update column selections here because they depend on the loaded data
	
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
   
		# Update lat/lon selectors
		self.lat_menu['values'] = [""] + columns
		lat_candidates = [col for col in columns if 'lat' in col.lower()]
		if lat_candidates:
			self.lat_column.set(lat_candidates[0])

		self.lon_menu['values'] = [""] + columns
		lon_candidates = [col for col in columns if 'lon' in col.lower()]
		if lon_candidates:
			self.lon_column.set(lon_candidates[0])

		# Update easting/northing selectors
		self.easting_menu['values'] = [""] + columns
		easting_candidates = [col for col in columns if 'east' in col.lower()]
		if easting_candidates:
			self.easting_column.set(easting_candidates[0])

		self.northing_menu['values'] = [""] + columns
		northing_candidates = [col for col in columns if 'north' in col.lower()]
		if northing_candidates:
			self.northing_column.set(northing_candidates[0])
		
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
		self.console.clear()
		
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
  
	def _complete_analysis_worker(self):
		"""Worker thread for running complete analysis (DEPRECATED - use CompleteAnalysisWorker instead)."""
		try:
			# Redirect stdout to console
			original_stdout = sys.stdout
			sys.stdout = self.redirector

			# 1. First run depth analysis
			print("Starting depth analysis...")
			
			# Load data
			data = self.data_loader.load_data(sheet_name=self.sheet_name.get())
			if data is None or data.empty:
				messagebox.showerror("Error", "Could not load data from the selected file.")
				self.set_status("Analysis failed")
				return
			
			# Set up analyzer
			self.depth_analyzer.set_data(data)
			self.depth_analyzer.set_columns(
				depth_column=self.depth_column.get(),
				kp_column=self.kp_column.get() if self.kp_column.get() else None,
				position_column=self.position_column.get() if self.position_column.get() else None
			)
			self.depth_analyzer.set_target_depth(self.target_depth.get())
			
			# Run depth analysis
			depth_success = self.depth_analyzer.analyze_data(
				max_depth=self.max_depth.get(),
				ignore_anomalies=self.ignore_anomalies.get()
			)
			
			if not depth_success:
				print("Depth analysis failed.")
				self.set_status("Depth analysis failed")
				return
			
			print("Depth analysis completed.")
			
			# 2. Run position analysis
			print("\nStarting position analysis...")
			
			# Set up position analyzer
			if not hasattr(self, 'position_analyzer'):
				from ..core.position_analyzer import PositionAnalyzer
				self.position_analyzer = PositionAnalyzer()
			
			self.position_analyzer.set_data(data)
			
			# Pass the new coordinate columns to the position analyzer
			self.position_analyzer.set_columns(
				kp_column=self.kp_column.get(),
				dcc_column=self.dcc_column.get() if hasattr(self, 'dcc_column') and self.dcc_column.get() else None,
				lat_column=self.lat_column.get() if self.lat_column.get() else None,
				lon_column=self.lon_column.get() if self.lon_column.get() else None,
				easting_column=self.easting_column.get() if self.easting_column.get() else None,
				northing_column=self.northing_column.get() if self.northing_column.get() else None
			)
			
			# Run position analysis
			position_success = self.position_analyzer.analyze_position_data()
			
			if not position_success:
				print("Position analysis failed.")
			else:
				print("Position analysis completed.")

			# Rest of the method remains the same
			# ...
		
		except Exception as e:
			import traceback
			print(f"Error during complete analysis: {str(e)}")
			print(traceback.format_exc())
			self.set_status("Analysis failed")
		finally:
			# Restore stdout
			sys.stdout = original_stdout
	
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
		self.console.clear()
		
		# Update status
		self.set_status("Running analysis...")
		
		# Redirect stdout to console
		original_stdout = sys.stdout
		sys.stdout = self.redirector
		
		# Run analysis in a separate thread to keep UI responsive
		self._run_analysis_thread()
	
	def _run_analysis_thread(self):
		"""Run depth analysis in a background thread using DepthAnalysisWorker."""
		# Prepare parameters for the worker
		params = {
			'file_path': self.file_path.get(),
			'output_dir': self.output_dir.get(),
			'depth_column': self.depth_column.get(),
			'kp_column': self.kp_column.get() if self.kp_column.get() else None,
			'position_column': self.position_column.get() if self.position_column.get() else None,
			'target_depth': self.target_depth.get(),
			'max_depth': self.max_depth.get(),
			'ignore_anomalies': self.ignore_anomalies.get(),
			'sheet_name': self.sheet_name.get(),
			'cable_id': self.cable_id.get() if self.cable_id.get() else None
		}
		
		# Create the worker
		worker = DepthAnalysisWorker(self, params)
		
		# Create and start thread
		analysis_thread = threading.Thread(target=worker.run)
		analysis_thread.daemon = True
		analysis_thread.start()
	
	def _analysis_worker(self):
		"""Worker function for background analysis (DEPRECATED - use DepthAnalysisWorker instead)."""
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
			self.depth_analyzer.set_data(data)
			self.depth_analyzer.set_columns(
				depth_column=self.depth_column.get(),
				kp_column=self.kp_column.get() if self.kp_column.get() else None,
				position_column=self.position_column.get() if self.position_column.get() else None
			)
			self.depth_analyzer.set_target_depth(self.target_depth.get())
			
			# 3. Run analysis
			print("Running analysis...")
			success = self.depth_analyzer.analyze_data(
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
				data=self.depth_analyzer.data,
				problem_sections=self.depth_analyzer.analysis_results.get('problem_sections', None)
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
			
			#6. Save outputs
			output_dir = self.output_dir.get()
			os.makedirs(output_dir, exist_ok=True)
			
			# Visualization
			viz_file = os.path.join(output_dir, "cable_burial_analysis.html")
			self.visualizer.save_visualization(viz_file)
			print(f"Interactive visualization saved to: {viz_file}")
			
			# Create Comprehensive report
			print("\nGenerating comprehensive report...")
			report_generator = ReportGenerator(self.output_dir.get())
			reports = report_generator.create_comprehensive_report(
			self.depth_analyzer.analysis_results,
			viz_file  # Now this variable is properly defined
			)
		
			print(f"Comprehensive Excel report saved to: {reports['excel_report']}")
			print(f"PDF summary report saved to: {reports['pdf_report']}")
   			
	  		# Analysis summary
			summary = self.depth_analyzer.get_analysis_summary()
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
			problem_sections = self.depth_analyzer.analysis_results.get('problem_sections', None)
			if problem_sections is not None and not problem_sections.empty:
				sections_file = os.path.join(output_dir, "problem_sections_report.xlsx")
				problem_sections.to_excel(sections_file, index=False)
				print(f"Problem sections report saved to: {sections_file}")
			
			anomalies = self.depth_analyzer.analysis_results.get('anomalies', None)
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
			
	def run_position_analysis(self):
		"""Run position analysis on the loaded data."""
		# Validate input parameters
		if not self.file_path.get():
			messagebox.showerror("Error", "Please select a file first.")
			return
		
		# Get position-related columns
		kp_column = None
		dcc_column = None
		lat_column = None
		lon_column = None
		easting_column = None
		northing_column = None
		
		# Auto-detect position columns from loaded data
		if self.data_loader.data is not None:
			columns = list(self.data_loader.data.columns)
			
			# Look for KP column
			kp_candidates = [col for col in columns if 'kp' in col.lower()]
			if kp_candidates:
				kp_column = kp_candidates[0]
			
			# Look for DCC column
			dcc_candidates = [col for col in columns if 'dcc' in col.lower()]
			if dcc_candidates:
				dcc_column = dcc_candidates[0]
		
		# Use user-selected columns if available
		if self.kp_column.get():
			kp_column = self.kp_column.get()
			
		if self.lat_column.get():
			lat_column = self.lat_column.get()
			
		if self.lon_column.get():
			lon_column = self.lon_column.get()
			
		if self.easting_column.get():
			easting_column = self.easting_column.get()
			
		if self.northing_column.get():
			northing_column = self.northing_column.get()
		
		# If no KP column was found, error
		if not kp_column:
			messagebox.showerror("Error", "Could not detect KP column. Position analysis requires a KP column.")
			return
		
		# Clear console
		self.console.clear()
		
		# Update status
		self.set_status("Running position analysis...")
		
		# Redirect stdout to console
		original_stdout = sys.stdout
		sys.stdout = self.redirector
		
		# Run analysis in a separate thread to keep UI responsive
		self._run_position_analysis_thread(
			kp_column, 
			dcc_column, 
			lat_column, 
			lon_column,
			easting_column,
			northing_column
		)

	def _run_position_analysis_thread(self, kp_column, dcc_column=None, lat_column=None, 
								lon_column=None, easting_column=None, northing_column=None):
		"""Run position analysis in a background thread using PositionAnalysisWorker."""
		# Prepare parameters for the worker
		params = {
			'file_path': self.file_path.get(),
			'output_dir': self.output_dir.get(),
			'kp_column': kp_column,
			'dcc_column': dcc_column,
			'lat_column': lat_column,
			'lon_column': lon_column,
			'easting_column': easting_column,
			'northing_column': northing_column,
			'sheet_name': self.sheet_name.get(),
			'cable_id': self.cable_id.get() if self.cable_id.get() else None
		}
		
		# Create the worker
		worker = PositionAnalysisWorker(self, params)
		
		# Create and start thread
		analysis_thread = threading.Thread(target=worker.run)
		analysis_thread.daemon = True
		analysis_thread.start()

	def run_complete_analysis(self):
		"""Run both depth and position analysis sequentially, then generate a comprehensive report."""
		# First check if we have the necessary input
		if not self.file_path.get():
			messagebox.showerror("Error", "Please select a file first.")
			return
		
		if not self.depth_column.get():
			messagebox.showerror("Error", "Please select a depth column.")
			return
		
		if not self.kp_column.get():
			messagebox.showerror("Error", "Please select a KP column for position analysis.")
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
		self.console.clear()
		
		# Update status
		self.set_status("Running complete analysis...")
		
		# Prepare parameters for the worker
		params = {
			'file_path': self.file_path.get(),
			'output_dir': self.output_dir.get(),
			'depth_column': self.depth_column.get(),
			'kp_column': self.kp_column.get(),
			'position_column': self.position_column.get() if self.position_column.get() else None,
			'lat_column': self.lat_column.get() if self.lat_column.get() else None,
			'lon_column': self.lon_column.get() if self.lon_column.get() else None,
			'easting_column': self.easting_column.get() if self.easting_column.get() else None,
			'northing_column': self.northing_column.get() if self.northing_column.get() else None,
			'target_depth': self.target_depth.get(),
			'max_depth': self.max_depth.get(),
			'ignore_anomalies': self.ignore_anomalies.get(),
			'sheet_name': self.sheet_name.get(),
			'kp_jump_threshold': 0.1,  # Could be made configurable
			'kp_reversal_threshold': 0.0001,  # Could be made configurable
			'cable_id': self.cable_id.get() if self.cable_id.get() else None
		}
		
		# Create the worker
		worker = CompleteAnalysisWorker(self, params)
		
		# Run as a separate thread to keep UI responsive
		analysis_thread = threading.Thread(target=worker.run)
		analysis_thread.daemon = True
		analysis_thread.start()

	def _complete_analysis_worker(self):
		"""Worker thread for running complete analysis."""
		try:
			# Redirect stdout to console
			original_stdout = sys.stdout
			sys.stdout = self.redirector

			# 1. First run depth analysis
			print("Starting depth analysis...")
			
			# Load data
			data = self.data_loader.load_data(sheet_name=self.sheet_name.get())
			if data is None or data.empty:
				messagebox.showerror("Error", "Could not load data from the selected file.")
				self.set_status("Analysis failed")
				return
			
			# Set up analyzer
			self.depth_analyzer.set_data(data)
			self.depth_analyzer.set_columns(
				depth_column=self.depth_column.get(),
				kp_column=self.kp_column.get() if self.kp_column.get() else None,
				position_column=self.position_column.get() if self.position_column.get() else None
			)
			self.depth_analyzer.set_target_depth(self.target_depth.get())
			
			# Run depth analysis
			depth_success = self.depth_analyzer.analyze_data(
				max_depth=self.max_depth.get(),
				ignore_anomalies=self.ignore_anomalies.get()
			)
			
			if not depth_success:
				print("Depth analysis failed.")
				self.set_status("Depth analysis failed")
				return
			
			print("Depth analysis completed.")
			
			# 2. Run position analysis
			print("\nStarting position analysis...")
			
			# Set up position analyzer
			if not hasattr(self, 'position_analyzer'):
				from ..core.position_analyzer import PositionAnalyzer
				self.position_analyzer = PositionAnalyzer()
			
			self.position_analyzer.set_data(data)
			self.position_analyzer.set_columns(
				kp_column=self.kp_column.get(),
				dcc_column=self.dcc_column.get() if hasattr(self, 'dcc_column') and self.dcc_column.get() else None,
				lat_column=self.lat_column.get() if hasattr(self, 'lat_column') and self.lat_column.get() else None,
				lon_column=self.lon_column.get() if hasattr(self, 'lon_column') and self.lon_column.get() else None
			)
			
			# Run position analysis
			position_success = self.position_analyzer.analyze_position_data()
			
			if not position_success:
				print("Position analysis failed.")
			else:
				print("Position analysis completed.")
				
				# Identify position problem sections
				sections = self.position_analyzer.identify_problem_sections()
				if not sections.empty:
					print(f"Identified {len(sections)} position problem sections.")
				
				# Save position analysis report
				output_dir = self.output_dir.get()
				os.makedirs(output_dir, exist_ok=True)
				
				pos_report_path = os.path.join(output_dir, "position_anomalies_report.xlsx")
				if 'position_analysis' in self.position_analyzer.analysis_results:
					self.position_analyzer.analysis_results['position_analysis'].to_excel(pos_report_path, index=False)
					print(f"Position anomalies report saved to: {pos_report_path}")
			
			# 3. Generate comprehensive report
			print("\nGenerating comprehensive report...")
			
			# Create directory if needed
			output_dir = self.output_dir.get()
			os.makedirs(output_dir, exist_ok=True)
			
			# Create visualization
			viz_file = os.path.join(output_dir, "cable_burial_analysis.html")
			
			# Set up visualizer
			self.visualizer.set_data(
				data=self.depth_analyzer.data,
				problem_sections=self.depth_analyzer.analysis_results.get('problem_sections', None)
			)
			self.visualizer.set_columns(
				depth_column=self.depth_column.get(),
				kp_column=self.kp_column.get() if self.kp_column.get() else None,
				position_column=self.position_column.get() if self.position_column.get() else None
			)
			self.visualizer.set_target_depth(self.target_depth.get())
			
			# Create visualization
			fig = self.visualizer.create_visualization(
				include_anomalies=True,
				segmented=(len(data) > 5000)
			)
			
			if fig is not None:
				self.visualizer.save_visualization(viz_file)
				print(f"Interactive visualization saved to: {viz_file}")
			
			# Generate comprehensive report
			from ..utils.report_generator import ReportGenerator
			report_generator = ReportGenerator(output_dir)
			
			# Combine analysis results
			combined_results = self.depth_analyzer.analysis_results.copy()
			
			# Add position analysis results
			if hasattr(self, 'position_analyzer') and hasattr(self.position_analyzer, 'analysis_results'):
				for key, value in self.position_analyzer.analysis_results.items():
					combined_results[f'position_{key}'] = value
			
			reports = report_generator.create_comprehensive_report(
				combined_results,
				viz_file if os.path.exists(viz_file) else None
			)
			
			if 'excel_report' in reports and reports['excel_report']:
				print(f"Comprehensive Excel report saved to: {reports['excel_report']}")
			
			if 'pdf_report' in reports and reports['pdf_report']:
				print(f"PDF summary report saved to: {reports['pdf_report']}")
			
			print("\nComplete analysis finished successfully.")
			self.set_status("Complete analysis finished")
		
		except Exception as e:
			import traceback
			print(f"Error during complete analysis: {str(e)}")
			print(traceback.format_exc())
			self.set_status("Analysis failed")
		finally:
			# Restore stdout
			sys.stdout = original_stdout

	def _position_analysis_worker(self, kp_column, dcc_column=None, lat_column=None, lon_column=None, easting_column=None, northing_column=None):
		"""Worker function for background position analysis (DEPRECATED - use PositionAnalysisWorker instead)."""
		try:
			# 1. Load the data
			print("Loading data...")
			data = self.data_loader.load_data(sheet_name=self.sheet_name.get())
			
			if data is None or data.empty:
				messagebox.showerror("Error", "Could not load data from the selected file.")
				self.set_status("Analysis failed")
				return
			
			# 2. Set up position analyzer
			print("Setting up position analysis...")
			self.position_analyzer.set_data(data)
			self.position_analyzer.set_columns(
				kp_column=kp_column,
				dcc_column=dcc_column,
				lat_column=lat_column,
				lon_column=lon_column,
				easting_column=easting_column,
				northing_column=northing_column
			)
			
			# 3. Run position analysis
			print("Running position analysis...")
			success = self.position_analyzer.analyze_position_data()
			
			if not success:
				messagebox.showerror("Analysis Error", "Position analysis failed.")
				self.set_status("Position analysis failed")
				return
			
			# 4. Identify problem sections
			print("Identifying position problem sections...")
			sections = self.position_analyzer.identify_problem_sections()
			
			# 5. Create visualization
			print("Creating position visualization...")
			fig = self.visualizer.create_position_visualization(
				data=self.position_analyzer.data,
				kp_column=kp_column,
				dcc_column=dcc_column
			)
			
			if fig is None:
				messagebox.showerror("Visualization Error", "Failed to create position visualization.")
				self.set_status("Visualization failed")
				return
			
			# 6. Save outputs
			output_dir = self.output_dir.get()
			os.makedirs(output_dir, exist_ok=True)
			
			# Visualization
			viz_file = os.path.join(output_dir, "position_quality_analysis.html")
			self.visualizer.figure = fig  # Set as current figure
			self.visualizer.save_visualization(viz_file)
			print(f"Interactive position visualization saved to: {viz_file}")
			
			# Position quality summary
			summary = self.position_analyzer.get_analysis_summary()
			print("\nPosition Analysis Summary:")
			print(f"Total data points: {summary.get('total_points', 0)}")
			print(f"KP range: {summary.get('kp_range', (0, 0))}")
			print(f"KP length: {summary.get('kp_length', 0):.3f} km")
			
			if 'quality_counts' in summary:
				quality_counts = summary['quality_counts']
				for quality, count in quality_counts.items():
					print(f"  {quality} quality: {count} points ({count/summary['total_points']*100:.1f}%)")
			
			if 'anomalies' in summary:
				anomalies = summary['anomalies']
				print("Position anomalies detected:")
				print(f"  KP jumps: {anomalies.get('kp_jumps', 0)}")
				print(f"  KP reversals: {anomalies.get('kp_reversals', 0)}")
				print(f"  KP duplicates: {anomalies.get('kp_duplicates', 0)}")
			
			# Export position anomalies to Excel if they exist
			position_anomalies = None
			if 'Is_KP_Jump' in self.position_analyzer.data.columns or 'Is_KP_Reversal' in self.position_analyzer.data.columns:
				# Filter the data to include only rows with position anomalies
				anomaly_mask = (
					# KP-related anomalies
					self.position_analyzer.data.get('Is_KP_Jump', False) | 
					self.position_analyzer.data.get('Is_KP_Reversal', False) | 
					self.position_analyzer.data.get('Is_KP_Duplicate', False) |
					# DCC-related anomalies
					self.position_analyzer.data.get('Is_Significant_Deviation', False) |
					# Low position quality (captures coordinate issues and combined problems)
					(self.position_analyzer.data.get('Position_Quality', 'Good') != 'Good')
				)
				position_anomalies = self.position_analyzer.data[anomaly_mask]
				
				if not position_anomalies.empty:
					anomalies_file = os.path.join(output_dir, "position_anomalies_report.xlsx")
					position_anomalies.to_excel(anomalies_file, index=False)
					print(f"Position anomalies report saved to: {anomalies_file}")
			
			# 7. Save Excel reports
			if hasattr(self.position_analyzer, 'analysis_results') and 'problem_sections' in self.position_analyzer.analysis_results:
				problem_sections = self.position_analyzer.analysis_results['problem_sections']
				if not problem_sections.empty:
					sections_file = os.path.join(output_dir, "position_problem_sections_report.xlsx")
					problem_sections.to_excel(sections_file, index=False)
					print(f"Position problem sections report saved to: {sections_file}")
			
			# 8. Update UI
			print("\nPosition analysis completed successfully.")
			self.set_status("Position analysis complete")
			
			# Ask to view results
			if messagebox.askyesno("Position Analysis Complete", 
								"Position analysis finished successfully. Open visualization?"):
				self.visualizer.open_visualization(viz_file)
			
		except Exception as e:
			import traceback
			print(f"Error during position analysis: {str(e)}")
			print(traceback.format_exc())
			messagebox.showerror("Position Analysis Error", f"An error occurred: {str(e)}")
			self.set_status("Position analysis failed")
	
	def _on_cable_selected(self, cable_id):
		"""
		Callback for when a cable is selected in the dropdown.
		
		Args:
			cable_id: The selected cable ID
		"""
		self.cable_id.set(cable_id)  # Store the selected cable ID for use in analysis
		self.set_status(f"Selected cable: {cable_id}")
		print(f"Selected cable: {cable_id}")
		
		# If the cable registry is available, get the cable type and status
		if hasattr(self, 'cable_frame') and hasattr(self.cable_frame, 'registry'):
			registry = self.cable_frame.registry
			
			# Get all cables matching this ID
			cables = registry.cables[registry.cables['cable_id'] == cable_id]
			
			if not cables.empty:
				cable_type = cables.iloc[0].get('type', '')
				cable_status = cables.iloc[0].get('status', '')
				print(f"Cable Type: {cable_type}, Status: {cable_status}")
				
				# This information could be included in reports and visualizations
	
	def _refresh_results(self):
		"""Refresh the results visualization and data."""
		# Check if results are available
		if hasattr(self, 'visualizer') and hasattr(self.visualizer, 'figure'):
			# Show the visualization container and hide placeholder
			self.viz_placeholder.pack_forget()
			self.viz_container.pack(fill="both", expand=True)
			
			# Update the visualization if needed
			# This would typically embed a visualization like a matplotlib figure
			
			# Update the results text
			if hasattr(self, 'depth_analyzer') and hasattr(self.depth_analyzer, 'analysis_results'):
				self._update_results_text(self.depth_analyzer.analysis_results)
		else:
			# Show placeholder
			self.viz_container.pack_forget()
			self.viz_placeholder.pack(fill="both", expand=True)

	def _update_results_text(self, results):
		"""Update the results text widget with analysis results."""
		if not hasattr(self, 'results_text'):
			return
			
		self.results_text.config(state="normal")
		self.results_text.delete(1.0, tk.END)
		
		# Format and display results summary
		if isinstance(results, dict):
			for key, value in results.items():
				if not isinstance(value, (pd.DataFrame, dict, list)):
					self.results_text.insert(tk.END, f"{key}: {value}\n")
		
		self.results_text.config(state="disabled")
 
	def _view_results(self, analysis_type="depth"):
		"""
		View analysis results with support for both depth and position analyses.
		
		Args:
			analysis_type: Type of analysis results to view ("depth" or "position")
		"""
		# Check if any analysis has been run
		depth_results = hasattr(self.depth_analyzer, 'analysis_results') and self.depth_analyzer.analysis_results
		position_results = hasattr(self.position_analyzer, 'analysis_results') and self.position_analyzer.analysis_results

		if not (depth_results or position_results):
			messagebox.showinfo("No Results", "Please run either depth or position analysis first.")
			return

		# Check if output directory exists
		output_dir = self.output_dir.get()
		if not os.path.exists(output_dir):
			messagebox.showerror("Error", "Output directory not found.")
			return

		# Create a selection dialog
		result_dialog = tk.Toplevel(self.root)
		result_dialog.title("View Analysis Results")
		result_dialog.geometry("300x200")

		# Result selection
		result_var = tk.StringVar(value="depth")
		
		ttk.Label(result_dialog, text="Select Analysis Results", font=("", 10, "bold")).pack(pady=(10,5))
		
		depth_radio = ttk.Radiobutton(
			result_dialog, 
			text="Depth Analysis", 
			variable=result_var, 
			value="depth",
			state="normal" if depth_results else "disabled"
		)
		depth_radio.pack(pady=5)
		
		position_radio = ttk.Radiobutton(
			result_dialog, 
			text="Position Analysis", 
			variable=result_var, 
			value="position",
			state="normal" if position_results else "disabled"
		)
		position_radio.pack(pady=5)

		def open_selected_results():
			"""Open the selected results in a web browser."""
			selected_type = result_var.get()
			
			if selected_type == "depth":
				viz_file = os.path.join(output_dir, "cable_burial_analysis.html")
			else:
				viz_file = os.path.join(output_dir, "position_quality_analysis.html")
			
			if not os.path.exists(viz_file):
				messagebox.showerror("Error", f"{selected_type.capitalize()} visualization file not found.")
				return
			
			result_dialog.destroy()
			self.visualizer.open_visualization(viz_file)

		# Buttons
		button_frame = ttk.Frame(result_dialog)
		button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
		
		ttk.Button(
			button_frame, 
			text="Open Visualization", 
			command=open_selected_results
		).pack(side="left", expand=True, padx=5)
		
		ttk.Button(
			button_frame, 
   
   
			text="Cancel", 
			command=result_dialog.destroy
		).pack(side="right", expand=True, padx=5)
  
	def _generate_comprehensive_report(self):
		"""Generate a comprehensive report from the latest analysis results."""
		# Check if analysis has been run
		if not hasattr(self.depth_analyzer, 'analysis_results') or not self.depth_analyzer.analysis_results:
			messagebox.showinfo("No Results", "Please run analysis first.")
			return
		
		# Get output directory
		output_dir = self.output_dir.get()
		if not os.path.exists(output_dir):
			# Prompt for output directory
			output_dir = filedialog.askdirectory(
				title="Select Output Directory for Comprehensive Report"
			)
			if not output_dir:
				return
			self.output_dir.set(output_dir)
		
		# Create the report generator
		report_generator = ReportGenerator(output_dir)
		
		# Get visualization path
		viz_file = os.path.join(output_dir, "cable_burial_analysis.html")
		
		# Generate comprehensive report
		self.set_status("Generating comprehensive report...")
		try:
			reports = report_generator.create_comprehensive_report(
				self.depth_analyzer.analysis_results,
				viz_file if os.path.exists(viz_file) else None
			)
			
			if reports['excel_report'] and reports['pdf_report']:
				if messagebox.askyesno("Report Generated", 
									"Comprehensive report generated successfully. Open report folder?"):
					import subprocess
					# Open folder based on platform
					if platform.system() == "Windows":
						os.startfile(output_dir)
					elif platform.system() == "Darwin":  # macOS
						subprocess.run(["open", output_dir])
					else:  # Linux
						subprocess.run(["xdg-open", output_dir])
			else:
				messagebox.showwarning("Report Generation", 
									"Some reports could not be generated. Check the console for details.")
		except Exception as e:
			import traceback
			print(f"Error generating report: {str(e)}")
			print(traceback.format_exc())
			messagebox.showerror("Report Error", f"Error generating report: {str(e)}")
		
		self.set_status("Ready")