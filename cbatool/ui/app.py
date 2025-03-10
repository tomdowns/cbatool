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
	OptionMenu, filedialog, messagebox, simpledialog, ttk, Menu, BooleanVar,Toplevel
)
import tkinter as tk

from ..core.data_loader import DataLoader
from ..core.analyzer import Analyzer
from ..core.visualizer import Visualizer
from ..utils.file_operations import select_file, open_file
from ..core.position_analyzer import PositionAnalyzer
from .dialogs import DataSelectionDialog, SettingsDialog, ConfigurationDialog
from ..ui.widgets import(
	CollapsibleFrame,
	CreateToolTip,
	ConsoleWidget,
	ScrollableFrame,
	StatusBar
)
from ..utils.config_manager import (
	load_configuration,
 	save_configuration,
	get_available_configurations,
	DEFAULT_CONFIG
)

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
		self.position_analyzer = PositionAnalyzer()
		
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
		self.sheet_name = StringVar(value="0")  # Default to first sheet
		self.ignore_anomalies = BooleanVar(value=False)
	
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
		
		# Input section - file selection, parameters
		input_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10 10 10 10")
		input_frame.pack(fill="x", pady=(0, 10))

		# File selection
		ttk.Label(input_frame, text="Data File:").grid(row=0, column=0, sticky="w", pady=5)
		ttk.Entry(input_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, sticky="ew", pady=5)
		ttk.Button(input_frame, text="Browse...", command=self._browse_file).grid(row=0, column=2, padx=5, pady=5)

		# Output directory
		ttk.Label(input_frame, text="Output Directory:").grid(row=1, column=0, sticky="w", pady=5)
		ttk.Entry(input_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, sticky="ew", pady=5)
		ttk.Button(input_frame, text="Browse...", command=self._browse_output_dir).grid(row=1, column=2, padx=5, pady=5)

		# Sheet selector
		ttk.Label(input_frame, text="Sheet Name:").grid(row=2, column=0, sticky="w", pady=5)
		self.sheet_menu = ttk.Combobox(input_frame, textvariable=self.sheet_name, state="readonly", width=15)
		self.sheet_menu.grid(row=2, column=1, sticky="w", pady=5)

		# Analysis Parameters Section
		analysis_params = CollapsibleFrame(input_frame, title="Analysis Parameters", expanded=True)
		analysis_params.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)

		# Create frames for each parameter group
		depth_frame = ttk.Frame(analysis_params.container)
		position_frame = ttk.Frame(analysis_params.container)

		# Depth Analysis Parameters
		depth_label = ttk.Label(depth_frame, text="Depth Analysis", font=("", 9, "bold"))
		depth_label.pack(anchor="w", pady=(0, 5))

		depth_params = ttk.Frame(depth_frame)
		depth_params.pack(fill="x", padx=10)

		ttk.Label(depth_params, text="Target Depth (m):").grid(row=0, column=0, sticky="w", pady=2)
		target_entry = ttk.Entry(depth_params, textvariable=self.target_depth, width=10)
		target_entry.grid(row=0, column=1, sticky="w", pady=2)
		CreateToolTip(target_entry, "Target burial depth for the cable")

		ttk.Label(depth_params, text="Max Trenching Depth (m):").grid(row=1, column=0, sticky="w", pady=2)
		max_entry = ttk.Entry(depth_params, textvariable=self.max_depth, width=10)
		max_entry.grid(row=1, column=1, sticky="w", pady=2)
		CreateToolTip(max_entry, "Maximum physically possible trenching depth")

		ttk.Label(depth_params, text="Depth Column:").grid(row=2, column=0, sticky="w", pady=2)
		self.depth_menu = ttk.Combobox(depth_params, textvariable=self.depth_column, state="readonly", width=15)
		self.depth_menu.grid(row=2, column=1, sticky="w", pady=2)
		CreateToolTip(self.depth_menu, "Column containing depth measurements")

		ignore_check = ttk.Checkbutton(depth_params, text="Ignore Anomalies", variable=self.ignore_anomalies)
		ignore_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
		CreateToolTip(ignore_check, "Exclude anomalous points from compliance analysis")

		# Position Analysis Parameters
		position_label = ttk.Label(position_frame, text="Position Analysis", font=("", 9, "bold"))
		position_label.pack(anchor="w", pady=(10, 5))

		position_params = ttk.Frame(position_frame)
		position_params.pack(fill="x", padx=10)

		ttk.Label(position_params, text="KP Column:").grid(row=0, column=0, sticky="w", pady=2)
		self.kp_menu = ttk.Combobox(position_params, textvariable=self.kp_column, state="readonly", width=15)
		self.kp_menu.grid(row=0, column=1, sticky="w", pady=2)
		CreateToolTip(self.kp_menu, "Column containing KP (kilometer point) values")

		ttk.Label(position_params, text="Position Column:").grid(row=1, column=0, sticky="w", pady=2)
		self.position_menu = ttk.Combobox(position_params, textvariable=self.position_column, state="readonly", width=15)
		self.position_menu.grid(row=1, column=1, sticky="w", pady=2)
		CreateToolTip(self.position_menu, "Column containing position values")

		# WGS84 coordinate system note
		ttk.Label(position_params, text="Note: Position analysis uses WGS84 coordinate system", 
				foreground="blue", font=("", 8, "italic")).grid(
				row=2, column=0, columnspan=2, sticky="w", pady=(0, 5))

		# Add the parameter frames to the collapsible section
		analysis_params.add(depth_frame)
		analysis_params.add(position_frame)

		# Configure grid column weights
		input_frame.columnconfigure(1, weight=1)
  
		# Button frame at the bottom
		button_frame = ttk.Frame(main_frame)
		button_frame.pack(fill="x", pady=10)

		# Analysis buttons
		ttk.Button(
			button_frame, 
			text="Run Depth Analysis",
			command=self.run_analysis
		).pack(side="left", padx=(0, 10))

		ttk.Button(
			button_frame,
			text="Run Position Analysis",
			command=self.run_position_analysis
		).pack(side="left", padx=(0, 10))

		ttk.Button(
			button_frame,
			text="View Results",
			command=self._view_results
		).pack(side="left", padx=(0, 10))

		ttk.Button(
			button_frame,
			text="Exit",
			command=self.root.destroy
		).pack(side="right")
  
		# Console output
		console_frame = ttk.LabelFrame(main_frame, text="Analysis Log", padding="10 10 10 10")
		console_frame.pack(fill="both", expand=True, pady=(0, 10))

		# Create ConsoleWidget
		self.console = ConsoleWidget(console_frame)
		self.console.pack(fill="both", expand=True)

		# Set up console redirector
		self.redirector = self.console.create_redirector()
	
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
		return {
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
			
			# Look for latitude column
			lat_candidates = [col for col in columns if 'lat' in col.lower()]
			if lat_candidates:
				lat_column = lat_candidates[0]
			
			# Look for longitude column
			lon_candidates = [col for col in columns if 'lon' in col.lower()]
			if lon_candidates:
				lon_column = lon_candidates[0]
		
		# If no columns were found, ask the user to select them
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
		self._run_position_analysis_thread(kp_column, dcc_column, lat_column, lon_column)

	def _run_position_analysis_thread(self, kp_column, dcc_column=None, lat_column=None, lon_column=None):
		"""Run position analysis in a background thread."""
		# Create and start thread
		analysis_thread = threading.Thread(
			target=self._position_analysis_worker,
			args=(kp_column, dcc_column, lat_column, lon_column)
		)
		analysis_thread.daemon = True
		analysis_thread.start()

	def _position_analysis_worker(self, kp_column, dcc_column=None, lat_column=None, lon_column=None):
		"""Worker function for background position analysis."""
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
				lon_column=lon_column
			)
			
			# 3. Run position analysis
			print("Running position analysis...")
			success = self.position_analyzer.analyze_position_data()
			
			if not success:
				messagebox.showerror("Analysis Error", "Position analysis failed.")
				self.set_status("Position analysis failed")
				return
			
			# 4. Identify problem segments
			print("Identifying position problem segments...")
			segments = self.position_analyzer.identify_problem_segments()
			
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
			if hasattr(self.position_analyzer, 'analysis_results') and 'problem_segments' in self.position_analyzer.analysis_results:
				problem_segments = self.position_analyzer.analysis_results['problem_segments']
				if not problem_segments.empty:
					segments_file = os.path.join(output_dir, "position_problem_segments_report.xlsx")
					problem_segments.to_excel(segments_file, index=False)
					print(f"Position problem segments report saved to: {segments_file}")
			
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
	
	def _view_results(self):
		"""
		View analysis results with support for both depth and position analyses.
		"""
		# Check if any analysis has been run
		depth_results = hasattr(self.analyzer, 'analysis_results') and self.analyzer.analysis_results
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