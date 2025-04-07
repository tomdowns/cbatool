"""
Custom widgets for CBAtool v2.0.

This module contains custom tkinter widgets used in the Cable Burial Analysis Tool GUI.
"""

import tkinter as tk
from tkinter import ttk
import logging
import sys
from typing import Optional, Callable, Any, Dict

# Configure logging
logger = logging.getLogger(__name__)


class ScrollableFrame(ttk.Frame):
	"""
	A frame with a scrollbar that allows its content to be scrollable.
	
	Attributes:
		scrollable_frame: The frame that can be scrolled.
	"""
	
	def __init__(self, parent, *args, **kwargs):
		"""
		Initialize a ScrollableFrame.
		
		Args:
			parent: The parent widget.
			*args: Additional positional arguments for the Frame.
			**kwargs: Additional keyword arguments for the Frame.
		"""
		super().__init__(parent, *args, **kwargs)
		
		# Create a canvas for scrolling
		self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
		scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
		
		# Create a frame inside the canvas for widgets
		self.scrollable_frame = ttk.Frame(self.canvas)
		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)
		
		# Add the inner frame to the canvas
		self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		
		# Configure the canvas to use the scrollbar
		self.canvas.configure(yscrollcommand=scrollbar.set)
		
		# Pack the scrollbar and canvas
		self.canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")
		
		# Make the canvas expand to fill the frame
		self.canvas.bind("<Configure>", self._on_canvas_configure)
		
	def _on_canvas_configure(self, event):
		"""Resize the inner frame to match the canvas size."""
		canvas_width = event.width
		self.canvas.itemconfig(self.canvas_frame, width=canvas_width)


class StatusBar(ttk.Frame):
	"""
	A status bar widget for displaying application status.
	
	Attributes:
		status_var: StringVar containing the current status message.
	"""
	
	def __init__(self, parent, *args, **kwargs):
		"""
		Initialize a StatusBar.
		
		Args:
			parent: The parent widget.
			*args: Additional positional arguments for the Frame.
			**kwargs: Additional keyword arguments for the Frame.
		"""
		super().__init__(parent, *args, **kwargs)
		
		# Create a label to display the status
		self.status_var = tk.StringVar(value="Ready")
		self.label = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(5, 2))
		self.label.pack(side="left", fill="x", expand=True)
		
		# Add a progress indicator
		self.progress = ttk.Progressbar(self, mode="indeterminate", length=100)
		self.progress.pack(side="right", padx=5)
		
	def set_status(self, message, show_progress=False):
		"""
		Set the status message and control the progress indicator.
		
		Args:
			message: The status message to display.
			show_progress: Whether to show the progress indicator.
		"""
		self.status_var.set(message)
		
		if show_progress:
			self.progress.start(10)
		else:
			self.progress.stop()
			self.progress.pack_forget()
			self.progress.pack(side="right", padx=5)


class LabeledEntry(ttk.Frame):
	"""
	A labeled entry widget that combines a label and an entry in a single widget.
	
	Attributes:
		label: The label widget.
		entry: The entry widget.
		variable: The variable bound to the entry.
	"""
	
	def __init__(self, parent, label_text, variable=None, width=20, **kwargs):
		"""
		Initialize a LabeledEntry.
		
		Args:
			parent: The parent widget.
			label_text: Text for the label.
			variable: Variable to bind to the entry.
			width: Width of the entry widget.
			**kwargs: Additional keyword arguments for the Frame.
		"""
		super().__init__(parent, **kwargs)
		
		# Create variable if not provided
		self.variable = variable if variable is not None else tk.StringVar()
		
		# Create label and entry
		self.label = ttk.Label(self, text=label_text)
		self.entry = ttk.Entry(self, textvariable=self.variable, width=width)
		
		# Grid layout
		self.label.grid(row=0, column=0, sticky="w", padx=(0, 5))
		self.entry.grid(row=0, column=1, sticky="ew")
		
		# Configure grid
		self.columnconfigure(1, weight=1)
		
	def get(self):
		"""Get the entry value."""
		return self.variable.get()
		
	def set(self, value):
		"""Set the entry value."""
		self.variable.set(value)


class ConsoleWidget(ttk.Frame):
	"""
	A widget for displaying console output with colorized text.
	
	Attributes:
		text: The text widget for displaying output.
	"""
	
	def __init__(self, parent, **kwargs):
		"""
		Initialize a ConsoleWidget.
		
		Args:
			parent: The parent widget.
			**kwargs: Additional keyword arguments for the Frame.
		"""
		super().__init__(parent, **kwargs)
		
		# Create text widget with scrollbar
		self.text = tk.Text(self, wrap="word", height=10, bg="#f0f0f0")
		scrollbar = ttk.Scrollbar(self, command=self.text.yview)
		
		# Configure text widget
		self.text.config(yscrollcommand=scrollbar.set)
		
		# Add text tags for colorization
		self.text.tag_configure("error", foreground="red")
		self.text.tag_configure("warning", foreground="orange")
		self.text.tag_configure("info", foreground="blue")
		self.text.tag_configure("success", foreground="green")
		
		# Pack widgets
		self.text.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")
		
	def clear(self):
		"""Clear the console."""
		self.text.delete(1.0, tk.END)
		
	def write(self, message, tag=None):
		"""
		Write a message to the console.
		
		Args:
			message: The message to write.
			tag: Optional tag for text styling.
		"""
		self.text.insert(tk.END, message, tag)
		self.text.see(tk.END)
		self.text.update_idletasks()
		
	def create_redirector(self):
		"""
		Create a console redirector for capturing stdout/stderr.
		
		Returns:
			ConsoleRedirector object.
		"""
		# Create a generic redirector class within this module
		class ConsoleRedirector:
			def __init__(self, text_widget):
				self.text_widget = text_widget
				self.stdout = sys.stdout
				self.buffer = ""
			
			def write(self, message):
				self.text_widget.insert("end", message)
				self.text_widget.see("end")
				self.stdout.write(message)
				self.buffer += message
			
			def flush(self):
				self.text_widget.update_idletasks()
				self.stdout.flush()
			
			def getvalue(self):
				return self.buffer
		
		return ConsoleRedirector(self.text)


class ToolbarButton(ttk.Button):
	"""A styled button for use in toolbars."""
	
	def __init__(self, parent, text, icon=None, command=None, **kwargs):
		"""
		Initialize a ToolbarButton.
		
		Args:
			parent: The parent widget.
			text: Text for the button.
			icon: Optional path to an icon image.
			command: Function to call when button is clicked.
			**kwargs: Additional keyword arguments for Button.
		"""
		super().__init__(parent, text=text, command=command, **kwargs)
		
		# Add icon if provided
		if icon:
			try:
				self.img = tk.PhotoImage(file=icon)
				self.config(image=self.img, compound="left")
			except Exception as e:
				logger.warning(f"Could not load icon {icon}: {e}")
	
class CollapsibleFrame(ttk.Frame):
	"""
	A frame that can be expanded or collapsed to show/hide its contents.

	Attributes:
		container: The frame that holds the content to be shown/hidden.
		expanded: Boolean indicating if the frame is expanded.
	"""

	def __init__(self, parent, title="Section", expanded=False, **kwargs):
		"""
		Initialize a CollapsibleFrame.
		
		Args:
			parent: The parent widget.
			title: Title for the collapsible section.
			expanded: Whether the section is initially expanded.
			**kwargs: Additional keyword arguments for the Frame.
		"""
		super().__init__(parent, **kwargs)
		
		# Create header frame
		self.header_frame = ttk.Frame(self)
		self.header_frame.pack(fill="x", expand=False)
		
		# Toggle button
		self.toggle_button = ttk.Button(
			self.header_frame, 
			text="▼" if expanded else "►",
			width=2,
			command=self.toggle
		)
		self.toggle_button.pack(side="left", padx=(0, 5))
		
		# Title label
		self.title_label = ttk.Label(
			self.header_frame, 
			text=title, 
			font=("", 10, "bold")
		)
		self.title_label.pack(side="left", fill="x", expand=True)
		
		# Content container
		self.container = ttk.Frame(self, padding=(15, 5, 5, 5))
		
		# Set initial state
		self.expanded = expanded
		if expanded:
			self.container.pack(fill="x", expand=True, pady=(5, 0))
		
	def toggle(self):
		"""Toggle between expanded and collapsed states."""
		self.expanded = not self.expanded
		
		if self.expanded:
			# Expand
			self.toggle_button.config(text="▼")
			self.container.pack(fill="x", expand=True, pady=(5, 0))
		else:
			# Collapse
			self.toggle_button.config(text="►")
			self.container.pack_forget()

	def add(self, widget):
		"""
		Add a widget to the container.
		
		Args:
			widget: The widget to add.
		"""
		widget.pack(fill="x", expand=True, pady=2)


class TabContainer(ttk.Notebook):
	"""
	A container widget that manages multiple tabs with a consistent interface.
	
	Attributes:
		tabs (Dict[str, ttk.Frame]): Dictionary mapping tab names to content frames.
		current_tab (str): Name of the currently selected tab.
	"""
	
	def __init__(self, parent, **kwargs):
		"""
		Initialize the TabContainer.
		
		Args:
			parent: The parent widget.
			**kwargs: Additional keyword arguments for ttk.Notebook.
		"""
		super().__init__(parent, **kwargs)
		self.tabs = {}
		self.current_tab = None
		
		# Bind tab change event
		self.bind("<<NotebookTabChanged>>", self._on_tab_changed)
		
	def add_tab(self, name, title, padding="15 15 15 15"):
		"""
		Add a new tab to the container.
		
		Args:
			name: Internal name for the tab.
			title: Display title for the tab.
			padding: Padding for the tab frame (defaults to "15 15 15 15").
			
		Returns:
			The frame for the tab content.
		"""
		frame = ttk.Frame(self, padding=padding)
		self.add(frame, text=title)
		self.tabs[name] = frame
		
		# If this is the first tab, set it as current
		if self.current_tab is None:
			self.current_tab = name
		
		return frame
		
	def select_tab(self, name):
		"""
		Select a tab by name.
		
		Args:
			name: Name of the tab to select.
		"""
		if name in self.tabs:
			self.select(self.index(self.tabs[name]))
			self.current_tab = name
		
	def disable_tab(self, name):
		"""
		Disable a tab by name.
		
		Args:
			name: Name of the tab to disable.
		"""
		if name in self.tabs:
			index = self.index(self.tabs[name])
			self.tab(index, state="disabled")
		
	def enable_tab(self, name):
		"""
		Enable a tab by name.
		
		Args:
			name: Name of the tab to enable.
		"""
		if name in self.tabs:
			index = self.index(self.tabs[name])
			self.tab(index, state="normal")
		
	def get_current_tab(self):
		"""
		Get the name of the currently selected tab.
		
		Returns:
			str: Name of the current tab.
		"""
		return self.current_tab
		
	def get_tab_frame(self, name):
		"""
		Get the frame for a specific tab.
		
		Args:
			name: Name of the tab.
		
		Returns:
			ttk.Frame: The tab's frame, or None if not found.
		"""
		return self.tabs.get(name, None)
		
	def _on_tab_changed(self, event):
		"""
		Handle tab change events.
		
		Args:
			event: Event details.
		"""
		# Get the selected tab index
		selected_index = self.index(self.select())
		
		# Find the corresponding tab name
		for name, frame in self.tabs.items():
			if self.index(frame) == selected_index:
				self.current_tab = name
				break


class CreateToolTip:
	"""
	Create a tooltip for a given widget.
	"""
	def __init__(self, widget, text="Tooltip"):
		self.widget = widget
		self.text = text
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.leave)
		self.tooltip = None

	def enter(self, event=None):
		x, y, _, _ = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 25
		
		# Create toplevel window
		self.tooltip = tk.Toplevel(self.widget)
		self.tooltip.wm_overrideredirect(True)
		self.tooltip.wm_geometry(f"+{x}+{y}")
		
		# Create tooltip content
		frame = ttk.Frame(self.tooltip, borderwidth=1, relief="solid")
		frame.pack(fill="both", expand=True)
		
		label = ttk.Label(frame, text=self.text, wraplength=250, padding=(5, 2), background="#ffffcc")
		label.pack()

	def leave(self, event=None):
		if self.tooltip:
			self.tooltip.destroy()
			self.tooltip = None