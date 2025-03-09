"""
Position visualization functions for CBAtool v2.0.

This module contains functions for visualizing position data quality and analysis results.
These functions complement the Visualizer class but focus specifically on position data.
"""

import os
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, List, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

def create_kp_continuity_plot(fig, data, kp_column, row=1, col=1, show_anomalies=True):
    """
    Add a KP continuity plot to an existing figure.
    
    Args:
        fig: Plotly figure object to add the plot to.
        data: DataFrame containing position analysis results.
        kp_column: Name of the KP column.
        row: Row in subplot grid.
        col: Column in subplot grid.
        show_anomalies: Whether to highlight anomalies.
        
    Returns:
        Updated figure.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.error("Plotly not available - visualization will be limited")
        return fig
    
    # Create index array for x-axis
    point_indices = list(range(len(data)))
    
    # Add main KP line
    fig.add_trace(
        go.Scatter(
            x=point_indices,
            y=data[kp_column],
            mode='lines',
            name='KP Progression',
            line=dict(color='blue', width=1)
        ),
        row=row, col=col
    )
    
    # Add anomalies if requested
    if show_anomalies and 'Is_KP_Jump' in data.columns:
        # Add KP jumps
        jump_indices = [i for i, jump in enumerate(data['Is_KP_Jump']) if jump]
        if jump_indices:
            fig.add_trace(
                go.Scatter(
                    x=[point_indices[i] for i in jump_indices],
                    y=data.iloc[jump_indices][kp_column],
                    mode='markers',
                    name='KP Jumps',
                    marker=dict(color='orange', size=8, symbol='triangle-up')
                ),
                row=row, col=col
            )
        
        # Add KP reversals
        reversal_indices = [i for i, rev in enumerate(data['Is_KP_Reversal']) if rev]
        if reversal_indices:
            fig.add_trace(
                go.Scatter(
                    x=[point_indices[i] for i in reversal_indices],
                    y=data.iloc[reversal_indices][kp_column],
                    mode='markers',
                    name='KP Reversals',
                    marker=dict(color='red', size=8, symbol='x')
                ),
                row=row, col=col
            )
    
    # Update layout for this subplot
    fig.update_xaxes(title_text="Point Index", row=row, col=col)
    fig.update_yaxes(title_text="KP Value", row=row, col=col)
    
    return fig

def create_cross_track_plot(fig, data, kp_column, dcc_column, quality_column='Position_Quality_Score', row=1, col=2):
    """
    Add a cross-track deviation plot to an existing figure.
    
    Args:
        fig: Plotly figure object to add the plot to.
        data: DataFrame containing position analysis results.
        kp_column: Name of the KP column.
        dcc_column: Name of the DCC column.
        quality_column: Name of the quality score column.
        row: Row in subplot grid.
        col: Column in subplot grid.
        
    Returns:
        Updated figure.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.error("Plotly not available - visualization will be limited")
        return fig
    
    # Add scatter plot with color based on quality
    fig.add_trace(
        go.Scatter(
            x=data[kp_column],
            y=data[dcc_column],
            mode='markers',
            marker=dict(
                size=5,
                color=data[quality_column],
                colorscale='RdYlGn',  # Red (poor) to Green (good)
                colorbar=dict(
                    title='Position Quality',
                    x=1.0,
                    y=0.5,
                    len=0.5
                ),
            ),
            name='Cross-Track Deviation'
        ),
        row=row, col=col
    )
    
    # Add zero line representing planned route
    fig.add_trace(
        go.Scatter(
            x=[data[kp_column].min(), data[kp_column].max()],
            y=[0, 0],
            mode='lines',
            line=dict(color='black', width=1, dash='dash'),
            name='Planned Route'
        ),
        row=row, col=col
    )
    
    # Update layout for this subplot
    fig.update_xaxes(title_text="KP", row=row, col=col)
    fig.update_yaxes(title_text="Cross-Track Deviation (m)", row=row, col=col)
    
    return fig

def create_quality_heatmap(fig, data, kp_column, quality_column='Position_Quality_Score', row=2, col=1):
    """
    Add a position quality heatmap to an existing figure.
    
    Args:
        fig: Plotly figure object to add the plot to.
        data: DataFrame containing position analysis results.
        kp_column: Name of the KP column.
        quality_column: Name of the quality score column.
        row: Row in subplot grid.
        col: Column in subplot grid.
        
    Returns:
        Updated figure.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.error("Plotly not available - visualization will be limited")
        return fig
    
    # Add heatmap-like visualization of position quality
    fig.add_trace(
        go.Scatter(
            x=data[kp_column],
            y=[0] * len(data),  # All at y=0
            mode='markers',
            marker=dict(
                size=10,
                color=data[quality_column],
                colorscale='RdYlGn',
                showscale=False
            ),
            name='Position Quality'
        ),
        row=row, col=col
    )
    
    # Add colored sections for problem segments if available
    if 'Segment_ID' in data.columns:
        segments = data.dropna(subset=['Segment_ID']).groupby('Segment_ID')
        
        for segment_id, group in segments:
            fig.add_trace(
                go.Scatter(
                    x=[group[kp_column].min(), group[kp_column].max()],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='red', width=5),
                    name=f'Problem Segment {int(segment_id)}'
                ),
                row=row, col=col
            )
    
    # Update layout for this subplot
    fig.update_xaxes(title_text="KP", row=row, col=col)
    fig.update_yaxes(title_text="", showticklabels=False, row=row, col=col)
    
    return fig

def create_position_dashboard(data, kp_column, dcc_column=None):
    """
    Create a comprehensive position quality dashboard.
    
    Args:
        data: DataFrame containing position analysis results.
        kp_column: Name of the KP column.
        dcc_column: Name of the DCC column (optional).
        
    Returns:
        Plotly figure object with the dashboard.
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        logger.error("Plotly not available - visualization will be limited")
        return None
    
    # Determine number of subplots based on available data
    rows = 2
    cols = 1
    if dcc_column and dcc_column in data.columns:
        cols = 2
    
    # Create subplot figure
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[
            'KP Progression', 
            'Cross-Track Deviation' if dcc_column else None,
            'Position Quality', 
            None
        ],
        vertical_spacing=0.1,
        horizontal_spacing=0.05
    )
    
    # Add KP continuity plot
    fig = create_kp_continuity_plot(fig, data, kp_column, row=1, col=1)
    
    # Add cross-track plot if DCC column is available
    if dcc_column and dcc_column in data.columns:
        fig = create_cross_track_plot(fig, data, kp_column, dcc_column, row=1, col=2)
    
    # Add position quality heatmap
    fig = create_quality_heatmap(fig, data, kp_column, row=2, col=1)
    
    # Update overall layout
    fig.update_layout(
        title="Position Quality Analysis",
        showlegend=True,
        height=800,
        width=1000
    )
    
    return fig