# CBATool UI Redesign Specification

## Overview

This document outlines the requirements and implementation details for restructuring the CBATool user interface using a tab-based approach. The redesign aims to address the current cramped layout while improving usability and maintaining all existing functionality.

## Current Issues

- UI elements are visually cramped and lack sufficient spacing
- Related controls are not clearly grouped
- Cable registry functionality needs better integration
- Configuration workflow is not intuitive

## Redesign Approach

The UI will be reorganized into three primary tabs to create a more logical workflow and provide adequate space for each component.

## Tab Structure

### Tab 1: Load Data

**Purpose:** Focus on data loading and output configuration.

**Components:**
- Data File selector with Browse button
- Output Directory selector with Browse button  
- Sheet Name dropdown selector
- Load Status indicator
- Load Data button (validates selections and enables other tabs when successful)

**Implementation Notes:**
- File path validation should occur when Browse button is clicked or when Load button is pressed
- Sheet Name dropdown should be populated after selecting a valid data file
- Success/failure of load operation should be clearly indicated
- Other tabs should be disabled until data is successfully loaded

### Tab 2: Analysis Parameters

**Purpose:** Configure depth and position analysis settings.

**Components:**
- **Depth Analysis section:**
  - Target Depth (m) input field
  - Max Trenching Depth (m) input field
  - Depth Column selector (populated based on loaded data)
  - Ignore Anomalies checkbox

- **Position Analysis section:**
  - KP Column selector
  - Position Column selector (optional)
  - Coordinate System selection:
    - Radio buttons for Lat/Long vs Easting/Northing
    - Conditional display of appropriate column selectors:
      - If Lat/Long: show Latitude Column and Longitude Column selectors
      - If Easting/Northing: show Easting Column and Northing Column selectors

**Implementation Notes:**
- Input validation for numeric fields
- Column selectors should display human-readable column names
- Default values should be applied based on previously saved configurations
- Field dependencies should be clearly indicated

### Tab 3: Cable Parameters

**Purpose:** Manage cable registry data and cable selection.

**Components:**
- Cable ID dropdown selector
- Filter controls:
  - Type dropdown (Power, Fiber, etc.)
  - Status dropdown (Active, Planned, Decommissioned, etc.)
- Cable Registry management buttons:
  - Import CSV button
  - Export CSV button
  - Add Cable button (opens dialog)
  - Edit Cable button (enabled when cable selected)
- Cable details panel (displays properties of selected cable)

**Implementation Notes:**
- Cable ID selector should be populated from cable_registry.py
- Filter controls should immediately update the Cable ID dropdown options
- Any changes to the registry should persist between sessions
- Import/Export should use standard CSV format described in cable_registry_specific.md

## Persistent UI Elements

The following elements should remain visible regardless of the active tab:

- Analysis execution buttons:
  - Run Complete Analysis
  - Run Depth Analysis
  - Run Position Analysis
- View Results button
- Progress indicator during analysis operations
- Status bar with current application state

## Implementation Requirements

### Code Structure

- Create a new TabContainer widget to manage tab switching
- Refactor existing UI code to use composable widget classes
- Move existing widgets into appropriate tab containers
- Ensure proper event handling between tabs

### Layout Guidelines

- Minimum 15px padding between UI elements
- Consistent alignment of labels and fields
- Grouping of related controls with visual separation
- Clear visual indication of the active tab
- Responsive layout that handles window resizing

### Integration with Existing Components

- Maintain compatibility with existing analysis workers
- Ensure cable registry integration with analysis parameters
- Update configuration management to handle the new UI structure
- Maintain support for all existing analysis operations

## Technical Implementation

This redesign should be implemented by:

1. Creating a new `TabContainer` class in `widgets.py`
2. Refactoring `app.py` to use the tab-based layout
3. Updating the configuration management to handle tab-specific settings
4. Enhancing the cable registry UI components with proper filtering

### Code Example for Tab Container

```python
class TabContainer(ttk.Notebook):
    """
    A container widget that manages multiple tabs with a consistent interface.
    
    Attributes:
        tabs (Dict[str, ttk.Frame]): Dictionary mapping tab names to content frames.
        current_tab (str): Name of the currently selected tab.
    """
    
    def __init__(self, parent, **kwargs):
        """Initialize the TabContainer."""
        super().__init__(parent, **kwargs)
        self.tabs = {}
        self.current_tab = None
        
    def add_tab(self, name, title):
        """
        Add a new tab to the container.
        
        Args:
            name: Internal name for the tab.
            title: Display title for the tab.
            
        Returns:
            The frame for the tab content.
        """
        frame = ttk.Frame(self, padding="10 10 10 10")
        self.add(frame, text=title)
        self.tabs[name] = frame
        return frame
        
    def select_tab(self, name):
        """
        Select a tab by name.
        
        Args:
            name: Name of the tab to select.
        """
        if name in self.tabs:
            tab_id = self.tabs[name]
            self.select(tab_id)
            self.current_tab = name
```

## Key Benefits

- **Improved Workflow:** Logical progression from data loading to analysis execution
- **Reduced Visual Clutter:** Each functional area has dedicated space
- **Better Cable Management:** Dedicated tab for cable registry operations
- **Enhanced Usability:** Clear separation of concerns with focused interfaces
- **Scalability:** Room for future feature additions without compromising the UI

## Implementation Strategy

1. Create prototype with basic tab structure
2. Migrate existing UI elements to appropriate tabs
3. Implement cable registry integration
4. Update configuration persistence
5. Test with various window sizes and data types
6. Finalize UI with consistent styling

## Alignment with Project Principles

This redesign aligns with core project principles:

- **DRY:** Reuse of widget components across tabs
- **KISS:** Simple, focused interfaces for each task
- **SOLID:** Single responsibility for each tab and component
- **Enterprise-grade:** Professional UI organization with improved workflow

By implementing this tab-based approach, the CBATool UI will significantly improve usability while maintaining all existing functionality and providing a foundation for future enhancements.
