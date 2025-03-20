# Position Analysis Enhancements Implementation Guide

This document outlines the planned enhancements for the position analysis feature in CBAtool v2.0, following DRY, KISS, YAGNI, and SOLID principles.

## Enhancements Overview

1. **WGS84 Coordinate System Comment**: Add information in the UI to inform users that positional analysis assumes WGS84 coordinate system.
2. **Easting/Northing Column Selection**: Allow users to select Easting and Northing columns for additional position analysis.
3. **Configurable DCC Threshold**: Add a user input for the maximum DCC deviation threshold.

## Detailed Implementation Approach

### 1. WGS84 Coordinate System Comment

**Files to modify**: `cbatool/ui/app.py`

**Implementation details**:
- Add a simple informational label in the configuration frame
- Place it near the position-related column selectors
- Keep text concise and informative

**Suggested code changes**:
```python
# Add after the position column selector in _create_widgets method
ttk.Label(input_frame, text="Note: Position analysis uses WGS84 coordinate system", 
          foreground="blue", font=("", 8, "italic")).grid(
          row=7, column=0, columnspan=2, sticky="w", pady=(0, 5))
```

### 2. Easting/Northing Column Selection

**Files to modify**:
- `cbatool/ui/app.py`
- `cbatool/core/position_analyzer.py`

**Implementation details**:
- Add UI elements for selecting Easting and Northing columns
- Enhance PositionAnalyzer to accept and use these parameters
- Keep existing lat/lon functionality

**Suggested code changes**:

a. **UI Changes** (in `app.py`):
```python
# Add in _create_variables method
self.easting_column = StringVar()
self.northing_column = StringVar()

# Add in _create_widgets method after position column selector
ttk.Label(input_frame, text="Easting Column:").grid(row=7, column=0, sticky="w", pady=5)
self.easting_menu = ttk.Combobox(input_frame, textvariable=self.easting_column, state="readonly", width=15)
self.easting_menu.grid(row=7, column=1, sticky="w", pady=5)

ttk.Label(input_frame, text="Northing Column:").grid(row=8, column=0, sticky="w", pady=5)
self.northing_menu = ttk.Combobox(input_frame, textvariable=self.northing_column, state="readonly", width=15)
self.northing_menu.grid(row=8, column=1, sticky="w", pady=5)

# Update _update_file_info method to populate easting and northing dropdowns
# Add after position_column assignment:
self.easting_menu['values'] = [""] + columns
easting_candidates = [col for col in columns if 'east' in col.lower()]
if easting_candidates:
    self.easting_column.set(easting_candidates[0])

self.northing_menu['values'] = [""] + columns
northing_candidates = [col for col in columns if 'north' in col.lower()]
if northing_candidates:
    self.northing_column.set(northing_candidates[0])

# Update run_position_analysis method to detect easting/northing columns
# Add after lon_column detection:
easting_column = None
northing_column = None

if self.easting_column.get():
    easting_column = self.easting_column.get()

if self.northing_column.get():
    northing_column = self.northing_column.get()

# Update _run_position_analysis_thread call to include new parameters
self._run_position_analysis_thread(kp_column, dcc_column, lat_column, lon_column, 
                                  easting_column, northing_column)
```

b. **Thread Worker Updates**:
```python
# Update _run_position_analysis_thread method signature
def _run_position_analysis_thread(self, kp_column, dcc_column=None, lat_column=None, 
                                lon_column=None, easting_column=None, northing_column=None, 
                                dcc_threshold=5.0):
    # Update thread creation
    analysis_thread = threading.Thread(
        target=self._position_analysis_worker,
        args=(kp_column, dcc_column, lat_column, lon_column, easting_column, northing_column, dcc_threshold)
    )
    # Rest remains the same

# Update _position_analysis_worker method signature
def _position_analysis_worker(self, kp_column, dcc_column=None, lat_column=None, 
                            lon_column=None, easting_column=None, northing_column=None, 
                            dcc_threshold=5.0):
    # Update set_columns call
    self.position_analyzer.set_columns(
        kp_column=kp_column,
        dcc_column=dcc_column,
        lat_column=lat_column,
        lon_column=lon_column,
        easting_column=easting_column,
        northing_column=northing_column
    )

    # Update analyze_position_data call
    success = self.position_analyzer.analyze_position_data(dcc_threshold=dcc_threshold)
```

c. **PositionAnalyzer Changes** (in `position_analyzer.py`):
```python
# Update set_columns method
def set_columns(self, kp_column: str, dcc_column: Optional[str] = None, 
               lat_column: Optional[str] = None, lon_column: Optional[str] = None,
               easting_column: Optional[str] = None, northing_column: Optional[str] = None) -> bool:
    # Add after existing column settings
    if easting_column and easting_column in self.data.columns:
        self.easting_column = easting_column
        logger.info(f"Using easting column: {easting_column}")
    else:
        self.easting_column = None
        
    if northing_column and northing_column in self.data.columns:
        self.northing_column = northing_column
        logger.info(f"Using northing column: {northing_column}")
    else:
        self.northing_column = None
        
    return True

# Update _analyze_coordinate_consistency method
def _analyze_coordinate_consistency(self, data: pd.DataFrame) -> pd.DataFrame:
    # Modify to use easting/northing if available, otherwise use lat/lon
    if self.easting_column and self.northing_column:
        logger.info("Analyzing coordinate consistency using Easting/Northing...")
        
        # Calculate distance using Easting/Northing (simpler than lat/lon)
        data['Easting_Diff'] = data[self.easting_column].diff()
        data['Northing_Diff'] = data[self.northing_column].diff()
        
        # Simple Euclidean distance
        data['Coord_Change'] = np.sqrt(data['Easting_Diff']**2 + data['Northing_Diff']**2)
        
        # Expected coordinate change based on KP difference (1 KP = 1000 meters)
        data['Expected_Coord_Change'] = data['KP_Diff'] * 1000
        
    elif self.lat_column and self.lon_column:
        # Existing lat/lon implementation
        # ...existing code...
    
    # Rest of the method remains the same
```

### 3. Configurable DCC Threshold

**Files to modify**:
- `cbatool/ui/app.py`
- `cbatool/core/position_analyzer.py`

**Implementation details**:
- Add UI element for DCC threshold
- Pass threshold to position analyzer
- Update analyzer to use the custom threshold

**Suggested code changes**:

a. **UI Changes** (in `app.py`):
```python
# Add in _create_variables method
self.dcc_threshold = DoubleVar(value=5.0)  # Default 5.0 meters

# Add in _create_widgets method (after DCC column selection)
ttk.Label(input_frame, text="DCC Threshold (m):").grid(row=9, column=0, sticky="w", pady=5)
ttk.Entry(input_frame, textvariable=self.dcc_threshold, width=10).grid(row=9, column=1, sticky="w", pady=5)

# Update run_position_analysis method
# Add before calling _run_position_analysis_thread:
dcc_threshold = self.dcc_threshold.get()

# Update thread function call
self._run_position_analysis_thread(kp_column, dcc_column, lat_column, lon_column, 
                                  easting_column, northing_column, dcc_threshold)
```

b. **PositionAnalyzer Changes** (in `position_analyzer.py`):
```python
# Update analyze_position_data method signature
def analyze_position_data(self, kp_jump_threshold: float = 0.1, 
                        kp_reversal_threshold: float = 0.0001,
                        dcc_threshold: float = 5.0) -> bool:
    # ...existing code...
    
    # Update cross-track deviation call
    if self.dcc_column:
        result = self._analyze_cross_track_deviation(result, threshold=dcc_threshold)
    
    # ...rest of the method remains the same...

# Update _analyze_cross_track_deviation method signature
def _analyze_cross_track_deviation(self, data: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    # Update logging message
    logger.info(f"Analyzing cross-track deviation (threshold: {threshold}m)...")
    
    # Use the threshold parameter in the calculations
    data['Is_Significant_Deviation'] = data['DCC_Abs'] > threshold
    
    # Update log message
    deviation_count = data['Is_Significant_Deviation'].sum()
    logger.info(f"Found {deviation_count} significant cross-track deviations (>{threshold}m)")
    
    # Use the parameter in the score calculation
    data['Cross_Track_Score'] = np.exp(-(data['DCC_Abs'] / threshold))
    
    return data
```

## Implementation Order

For a smooth implementation process, follow this order:

1. First, add the WGS84 coordinate system comment (smallest change)
2. Next, implement the configurable DCC threshold
3. Finally, add the Easting/Northing column selection support

This approach allows for incremental testing and ensures each feature works properly before moving to the next.

## Testing Checklist

After implementation, verify:

- [ ] The WGS84 note is visible and properly formatted
- [ ] Easting/Northing column selectors appear and correctly populate
- [ ] Position analysis works with only lat/lon (backwards compatibility)
- [ ] Position analysis works with only easting/northing 
- [ ] Position analysis works with both coordinate types
- [ ] DCC threshold input accepts decimal values
- [ ] Changing DCC threshold affects the analysis results appropriately
- [ ] All reports and visualizations work correctly with the new features