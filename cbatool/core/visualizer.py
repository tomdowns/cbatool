
"""
Visualizer module for CBAtool v2.0.

This module contains the Visualizer class responsible for creating interactive
visualizations of cable burial data analysis results.
"""

import os
import webbrowser
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

class Visualizer:
	"""
	Class for creating interactive visualizations of cable burial data analysis.
	
	Attributes:
		data (pd.DataFrame): The data to visualize.
		problem_sections (pd.DataFrame): Information about problem sections.
		depth_column (str): Name of the column containing depth measurements.
		kp_column (str): Name of the column containing KP values.
		position_column (str): Name of the column containing position values.
		target_depth (float): Target burial depth for compliance checking.
		figure: The visualization figure object.
	"""
	
	def __init__(self):
		"""Initialize the Visualizer."""
		self.data = None
		self.problem_sections = None
		self.depth_column = None
		self.kp_column = None
		self.position_column = None
		self.target_depth = 1.5  # Default target depth in meters
		self.figure = None
		
		# Try to import plotly
		try:
			import plotly.graph_objects as go
			from plotly.subplots import make_subplots
			self.plotly_available = True
		except ImportError:
			logger.warning("Plotly not available - visualization will be limited")
			self.plotly_available = False
	
	def set_data(self, data: pd.DataFrame, problem_sections: Optional[pd.DataFrame] = None) -> bool:
		"""
		Set the data to visualize.
		
		Args:
			data: DataFrame containing analyzed cable burial data.
			problem_sections: DataFrame containing problem section information.
			
		Returns:
			bool: True if data was set successfully, False otherwise.
		"""
		if data is None or data.empty:
			logger.error("Cannot set empty data for visualization")
			return False
			
		self.data = data
		
		if problem_sections is not None:
			self.problem_sections = problem_sections
			
		logger.info(f"Data set for visualization: {len(data)} rows")
		return True
	
	def set_columns(self, depth_column: str, kp_column: Optional[str] = None, 
				  position_column: Optional[str] = None) -> bool:
		"""
		Set the column names to use for visualization.
		
		Args:
			depth_column: Name of the column containing depth measurements.
			kp_column: Name of the column containing KP values (optional).
			position_column: Name of the column containing position values (optional).
			
		Returns:
			bool: True if columns were set successfully, False otherwise.
		"""
		if self.data is None:
			logger.error("No data loaded for column setting")
			return False
			
		# Validate depth column exists
		if depth_column not in self.data.columns:
			logger.error(f"Depth column '{depth_column}' not found in data")
			return False
			
		self.depth_column = depth_column
		logger.info(f"Using depth column for visualization: {depth_column}")
		
		# Validate KP column if provided
		if kp_column and kp_column in self.data.columns:
			self.kp_column = kp_column
			logger.info(f"Using KP column for visualization: {kp_column}")
		else:
			self.kp_column = None
			if kp_column:  # Only log error if a column was specified but not found
				logger.warning(f"KP column '{kp_column}' not found in data")
		
		# Validate position column if provided
		if position_column and position_column in self.data.columns:
			self.position_column = position_column
			logger.info(f"Using position column for visualization: {position_column}")
		else:
			self.position_column = None
			if position_column:  # Only log error if a column was specified but not found
				logger.warning(f"Position column '{position_column}' not found in data")
				
		return True
	
	def set_target_depth(self, target_depth: float) -> None:
		"""
		Set the target burial depth for visualization.
		
		Args:
			target_depth: Target depth in meters.
		"""
		self.target_depth = target_depth
		logger.info(f"Target depth for visualization set to {target_depth}m")
	
	def create_visualization(self, include_anomalies: bool = True, 
						   segmented: bool = False) -> Any:
		"""
		Create an interactive visualization of burial depth with problem areas highlighted.
		
		Args:
			include_anomalies: Whether to highlight anomalies on the chart.
			segmented: Whether to create a segmented visualization for very large datasets.
			
		Returns:
			Plotly figure object with the interactive visualization.
		"""
		if not self.plotly_available:
			logger.error("Plotly is not available - cannot create visualization")
			return None
			
		if self.data is None or self.depth_column is None:
			logger.error("Data or depth column not set for visualization")
			return None
			
		# Import plotly here to ensure it's available
		import plotly.graph_objects as go
		from plotly.subplots import make_subplots
		
		logger.info("Creating interactive visualization...")
		
		# Determine what to use for x-axis
		if self.kp_column and self.kp_column in self.data.columns:
			x_values = self.data[self.kp_column]
			x_label = 'Cable Position (KP)'
			hover_pos_label = 'KP'
		elif self.position_column and self.position_column in self.data.columns:
			x_values = self.data[self.position_column]
			x_label = f'Cable Position ({self.position_column})'
			hover_pos_label = self.position_column
		else:
			x_values = self.data.index
			x_label = 'Cable Position (Index)'
			hover_pos_label = 'Position'
		
		if segmented and len(self.data) > 5000:
			fig = self._create_segmented_visualization(x_values, hover_pos_label, include_anomalies)
		else:
			fig = self._create_standard_visualization(x_values, hover_pos_label, include_anomalies)
		
		# Update common layout
		fig.update_layout(
			title={
				'text': 'Cable Burial Depth Analysis',
				'y': 0.95,
				'x': 0.5,
				'xanchor': 'center',
				'yanchor': 'top'
			},
			xaxis_title=x_label,
			yaxis_title='Depth (m)',
			yaxis=dict(
				autorange="reversed",  # Invert y-axis so deeper is lower
				zeroline=True,
				zerolinecolor='rgba(0,0,0,1)',
				gridcolor='rgba(0,0,0,0.05)'
			),
			xaxis=dict(
				zeroline=True,
				zerolinecolor='rgba(0,0,0,0.2)',
				gridcolor='rgba(0,0,0,0.1)'
			),
			hovermode='closest',
			legend_title='Legend',
			plot_bgcolor='white',
			margin=dict(l=50, r=50, t=80, b=50),
			height=600
		)
		
		# Add useful annotations
		if 'Is_Anomaly' in self.data.columns:
			anomaly_count = self.data['Is_Anomaly'].sum()
			if anomaly_count > 0:
				fig.add_annotation(
					text=f"{anomaly_count} anomalous data points detected",
					align="left",
					showarrow=False,
					xref="paper",
					yref="paper",
					x=0.02,
					y=0.02,
					bgcolor="rgba(255,255,255,0.8)",
					bordercolor="red",
					borderwidth=1
				)
		
		if self.problem_sections is not None and not self.problem_sections.empty:
			section_count = len(self.problem_sections)
			
			# If total_problem_length exists, include it
			if 'Length_Meters' in self.problem_sections.columns:
				total_length = self.problem_sections['Length_Meters'].sum()
				fig.add_annotation(
					text=f"{section_count} non-compliant sections (total: {total_length:.1f}m)",
					align="right",
					showarrow=False,
					xref="paper",
					yref="paper",
					x=0.98,
					y=0.02,
					bgcolor="rgba(255,255,255,0.8)",
					bordercolor="orange",
					borderwidth=1
				)
		
		self.figure = fig
		return fig
	
	def _create_standard_visualization(self, x_values, hover_pos_label, include_anomalies):
		"""Create a standard (non-segmented) visualization."""
		import plotly.graph_objects as go
		
		# Create main figure
		fig = go.Figure()
		
		# Add depth profile trace
		fig.add_trace(
			go.Scatter(
				x=x_values,
				y=self.data[self.depth_column],
				mode='lines',
				line=dict(color='brown', width=1),
				name='Burial Depth',
				hovertemplate=(
					f"{hover_pos_label}: %{{x}}<br>"
					f"Depth: %{{y:.2f}}m<extra></extra>"
				)
			)
		)
		
		# Add target depth line
		fig.add_trace(
			go.Scatter(
				x=[x_values.min(), x_values.max()],
				y=[self.target_depth, self.target_depth],
				mode='lines',
				line=dict(color='green', width=1, dash='dash'),
				name=f'Target Depth ({self.target_depth}m)',
				hoverinfo='name'
			)
		)
		
		# Add problem section highlighting if we have problem sections
		if self.problem_sections is not None and not self.problem_sections.empty:
			self._add_problem_section_highlighting(fig, x_values)
		
		# Add anomaly markers if requested and available
		if include_anomalies and 'Is_Anomaly' in self.data.columns:
			self._add_anomaly_markers(fig, x_values, hover_pos_label)
			
		return fig
	
	def _add_anomaly_markers(self, fig, x_values, hover_pos_label):
		"""Add anomaly markers to the visualization."""
		import plotly.graph_objects as go
		
		# If no anomalies column exists, return without adding markers
		if 'Is_Anomaly' not in self.data.columns:
			return
			
		# Get all anomalous points
		anomalies = self.data[self.data['Is_Anomaly']]
		
		if len(anomalies) == 0:
			return
			
		# Track which anomaly types we've added to avoid duplicate legend entries
		added_anomaly_types = set()
		
		# Define marker styles for different anomaly types
		marker_styles = {
			'Exceeds maximum trenching depth': dict(
				symbol='x', size=12, color='red', line=dict(width=2, color='darkred')
			),
			'Invalid depth (below minimum)': dict(
				symbol='x', size=12, color='red', line=dict(width=2, color='darkred')
			),
			'Sudden depth change': dict(
				symbol='triangle-up', size=10, color='orange', line=dict(width=1, color='darkorange')
			),
			'Statistical outlier': dict(
				symbol='circle', size=8, color='gold', line=dict(width=1, color='goldenrod')
			),
			'Unknown anomaly': dict(
				symbol='circle', size=8, color='gray', line=dict(width=1, color='gray')
			)
		}
		
		# Group anomalies by their type
		if 'Anomaly_Type' in anomalies.columns:
			# Group anomalies by their first word to match the marker styles
			def get_anomaly_key(anomaly_type):
				if not anomaly_type:
					return 'Unknown anomaly'
				for key in marker_styles.keys():
					if str(anomaly_type).startswith(key.split('(')[0].strip()):
						return key
				return 'Unknown anomaly'
			
			# Add a temporary key column for grouping
			anomalies['Anomaly_Key'] = anomalies['Anomaly_Type'].apply(get_anomaly_key)
			
			# Add traces for each anomaly type
			for anomaly_key, group in anomalies.groupby('Anomaly_Key'):
				# Get x values for this group
				if self.kp_column and self.kp_column in group.columns:
					group_x = group[self.kp_column]
				elif self.position_column and self.position_column in group.columns:
					group_x = group[self.position_column]
				else:
					group_x = group.index
				
				# Get marker style
				marker = marker_styles.get(
					anomaly_key, 
					dict(symbol='circle', size=8, color='gray')
				)
				
				# Create hover text
				hover_text = [
					f"{hover_pos_label}: {x}<br>"
					f"Depth: {row[self.depth_column]:.2f}m<br>"
					f"<b>Anomaly:</b> {row['Anomaly_Type']}"
					for x, (_, row) in zip(group_x, group.iterrows())
				]
				
				# Add the trace
				fig.add_trace(
					go.Scatter(
						x=group_x,
						y=group[self.depth_column],
						mode='markers',
						marker=marker,
						name=anomaly_key,
						hovertext=hover_text,
						hoverinfo='text'
					)
				)
		else:
			# If no Anomaly_Type column, just add all anomalies as a single group
			marker = dict(symbol='circle', size=8, color='red')
			fig.add_trace(
				go.Scatter(
					x=x_values[self.data['Is_Anomaly']],
					y=self.data.loc[self.data['Is_Anomaly'], self.depth_column],
					mode='markers',
					marker=marker,
					name='Anomaly',
					hoverinfo='y'
				)
			)
		
		return fig  
	
	def _create_segmented_visualization(self, x_values, hover_pos_label, include_anomalies):
		"""Create a segmented visualization for large datasets."""
		import plotly.graph_objects as go
		from plotly.subplots import make_subplots
		
		# Calculate number of segments (aim for ~1000 points per segment)
		segment_size = 1000
		num_segments = max(1, int(np.ceil(len(self.data) / segment_size)))
		
		logger.info(f"Creating segmented visualization with {num_segments} segments")
		
		# Create figure with subplot for each segment
		fig = make_subplots(
			rows=num_segments,
			cols=1,
			shared_xaxes=False,
			vertical_spacing=0.02,
			subplot_titles=[f"Segment {i+1}" for i in range(num_segments)]
		)
		
		# Add data for each segment
		for i in range(num_segments):
			start_idx = i * segment_size
			end_idx = min((i + 1) * segment_size, len(self.data))
			
			segment_data = self.data.iloc[start_idx:end_idx]
			segment_x = x_values.iloc[start_idx:end_idx] if hasattr(x_values, 'iloc') else x_values[start_idx:end_idx]
			
			# Add depth profile trace
			fig.add_trace(
				go.Scatter(
					x=segment_x,
					y=segment_data[self.depth_column],
					mode='lines',
					line=dict(color='brown', width=1),
					name='Burial Depth' if i == 0 else f'Burial Depth (Segment {i+1})',
					showlegend=(i == 0),  # Only show in legend for first segment
					hovertemplate=(
						f"{hover_pos_label}: %{{x}}<br>"
						f"Depth: %{{y:.2f}}m<extra></extra>"
					)
				),
				row=i+1,
				col=1
			)
			
			# Add target depth line
			fig.add_trace(
				go.Scatter(
					x=[segment_x.min(), segment_x.max()],
					y=[self.target_depth, self.target_depth],
					mode='lines',
					line=dict(color='green', width=1, dash='dash'),
					name=f'Target Depth ({self.target_depth}m)' if i == 0 else f'Target Depth (Segment {i+1})',
					showlegend=(i == 0),  # Only show in legend for first segment
					hoverinfo='name'
				),
				row=i+1,
				col=1
			)
			
			# Set y-axis to be reversed (deeper is lower)
			fig.update_yaxes(autorange="reversed", row=i+1, col=1)
		
		return fig
	
	def _add_problem_section_highlighting(self, fig, x_values):
		"""Add problem section highlighting to the figure."""
		import plotly.graph_objects as go
		
		# Get position column names from the problem sections DataFrame
		if 'Position_Type' not in self.problem_sections.columns:
			logger.warning("Cannot add problem section highlighting - missing Position_Type column")
			return
			
		pos_type = self.problem_sections['Position_Type'].iloc[0]  # Use the first one's type
		start_col = f'Start_{pos_type}'
		end_col = f'End_{pos_type}'
		
		if start_col not in self.problem_sections.columns or end_col not in self.problem_sections.columns:
			logger.warning(f"Cannot add problem section highlighting - missing {start_col} or {end_col} columns")
			return
		
		# Add shapes for each severity level with different colors
		severity_colors = {
			'High': 'rgba(255, 0, 0, 0.3)',    # Red
			'Medium': 'rgba(255, 165, 0, 0.2)', # Orange
			'Low': 'rgba(255, 255, 0, 0.15)'    # Yellow
		}
		
		# Track which severities we've added to avoid duplicate legend entries
		added_severities = set()
		
		for _, section in self.problem_sections.iterrows():
			severity = section['Severity']
			color = severity_colors.get(severity, 'rgba(128, 128, 128, 0.2)')
			
			# Add rectangle shape for this section
			fig.add_shape(
				type="rect",
				x0=section[start_col],
				x1=section[end_col],
				y0=self.data[self.depth_column].min() * 0.9,  # Extend below the chart
				y1=0,  # Up to the surface (y-axis will be inverted)
				fillcolor=color,
				opacity=0.5,
				layer="below",
				line_width=0
			)
			
			# Add to legend if we haven't seen this severity before
			if severity not in added_severities:
				fig.add_trace(
					go.Scatter(
						x=[None],
						y=[None],
						mode='markers',
						marker=dict(
							size=10,
							color=color.replace('0.3', '1').replace('0.2', '1').replace('0.15', '1')
						),
						name=f'{severity} Severity Area',
						showlegend=True
					)
				)
				added_severities.add(severity)
	def create_position_visualization(self, data, kp_column, dcc_column=None):
		"""
		Create a visualization specifically for position data quality.
		
		Args:
			data: DataFrame containing position analysis results.
			kp_column: Name of the KP column.
			dcc_column: Name of the DCC column (optional).
			
		Returns:
			Plotly figure object with the position visualization.
		"""
		if not self.plotly_available:
			logger.error("Plotly is not available - cannot create visualization")
			return None
			
		# Import from the position visualizer module
		from .position_visualizer import create_position_dashboard
		
		# Create the dashboard
		fig = create_position_dashboard(data, kp_column, dcc_column)
	
		return fig
			
	def save_visualization(self, output_file):
		"""
		Save the interactive visualization to an HTML file.
		
		Args:
			output_file: Path where the HTML file should be saved.
			
		Returns:
			bool: True if successful, False otherwise.
		"""
		if not self.figure:
			logger.error("No visualization to save")
			return False
			
		try:
			# Create directory if needed
			output_dir = os.path.dirname(output_file)
			if output_dir and not os.path.exists(output_dir):
				os.makedirs(output_dir)
			
			# Save the figure
			self.figure.write_html(
				output_file,
				include_plotlyjs='cdn',  # Use CDN version of plotly.js (smaller file)
				full_html=True,
				config={
					'responsive': True,
					'displayModeBar': True,
					'modeBarButtonsToAdd': ['drawline', 'eraseshape']
				}
			)
			logger.info(f"Visualization saved to: {output_file}")
			return True
		except Exception as e:
			logger.error(f"Failed to save visualization: {str(e)}")
			return False

	def open_visualization(self, html_file):
		"""
		Open the visualization HTML file in the default web browser.
		
		Args:
			html_file: Path to the HTML file to open.
			
		Returns:
			bool: True if successful, False otherwise.
		"""
		try:
			if not os.path.exists(html_file):
				logger.error(f"Visualization file not found: {html_file}")
				return False
				
			# Open the HTML file in the default web browser
			logger.info(f"Opening visualization in browser: {html_file}")
			webbrowser.open('file://' + os.path.abspath(html_file))
			return True
		except Exception as e:
			logger.error(f"Failed to open visualization: {str(e)}")
			return False