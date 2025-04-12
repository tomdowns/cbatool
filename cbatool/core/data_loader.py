# -*- coding: utf-8 -*-
"""
DataLoader module for CBAtool v2.0.

This module contains the DataLoader class responsible for loading data from various
file formats, with a focus on Excel files containing cable burial data.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

class DataLoader:
    """
    Class for loading cable data from files, with robust error handling and diagnostics.

    Attributes:
        file_path (str): Path to the data file.
        data (pd.DataFrame): Loaded data.
        sheet_names (List[str]): Names of available sheets in Excel file.
        column_info (Dict): Information about columns in the data.
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the DataLoader with optional file path.

        Args:
            file_path: Path to the data file (optional).
        """
        self.file_path: Optional[str] = None
        self.data: Optional[pd.DataFrame] = None
        self.sheet_names: List[str] = []
        self.column_info: Dict[str, Any] = {} # Use Any for flexibility

        # Load file info if path is provided
        if file_path:
            self.set_file_path(file_path)

    def set_file_path(self, file_path: str) -> bool:
        """
        Set the file path and read basic file information.

        Args:
            file_path: Path to the data file.

        Returns:
            bool: True if file information was loaded successfully, False otherwise.
        """
        # Validate file exists
        if not file_path or not isinstance(file_path, str):
             logger.error("Invalid file path provided.")
             return False
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            self.file_path = None # Clear path if invalid
            self.sheet_names = []
            return False

        self.file_path = file_path
        # Reset data when file path changes
        self.data = None
        self.column_info = {}
        return self._read_file_info()

    def _read_file_info(self) -> bool:
        """
        Read basic information from the file (e.g., sheet names).

        Returns:
            bool: True if file information was loaded successfully, False otherwise.
        """
        if not self.file_path: return False
        try:
            # Reset sheet names
            self.sheet_names = []
            file_lower = self.file_path.lower()

            if file_lower.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')): # Broader Excel support
                # Use openpyxl engine explicitly for better compatibility if available
                engine = 'openpyxl' if file_lower.endswith('.xlsx') else None
                try:
                     # Reading only sheet names shouldn't trigger warnings often
                     with pd.ExcelFile(self.file_path, engine=engine) as excel_file:
                         self.sheet_names = excel_file.sheet_names
                except Exception as e_inner:
                     logger.warning(f"Could not read sheet names with default/openpyxl engine: {e_inner}. Trying without engine hint.")
                     # Fallback without engine hint
                     with pd.ExcelFile(self.file_path) as excel_file:
                          self.sheet_names = excel_file.sheet_names

                logger.info(f"Found sheets: {self.sheet_names}")
                return True
            elif file_lower.endswith('.csv'):
                self.sheet_names = ['Sheet1']  # CSV has only one effective sheet
                logger.info("CSV file detected, using default sheet name 'Sheet1'")
                return True
            else:
                logger.warning(f"Unsupported file extension for reading info: {self.file_path}")
                return False
        except Exception as e:
            logger.error(f"Error reading file information from '{self.file_path}': {e}", exc_info=True)
            return False

    # --- MODIFIED SIGNATURE ---
    def load_data(self, sheet_name: Union[str, int, None] = 0, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Load data from the specified file and sheet.

        Args:
            sheet_name: Name or index of the sheet to load (default is 0).
                        Use None to attempt loading without specifying sheet (for single-sheet files).
            nrows: Number of rows to read (None reads all rows).

        Returns:
            DataFrame containing the loaded data, or None if loading failed.
        """
        if not self.file_path:
            logger.error("No file path set for DataLoader.")
            return None

        # Use provided sheet_name or default to 0 if None was explicitly passed
        # This allows flexibility for single-sheet excel files or CSVs
        effective_sheet_name = sheet_name if sheet_name is not None else 0

        logger.info(f"Loading data from '{os.path.basename(self.file_path)}', "
                    f"Sheet: '{effective_sheet_name}', Nrows: {nrows or 'All'}")

        try:
            file_lower = self.file_path.lower()
            df = None
            if file_lower.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
                # --- Pass nrows to helper ---
                df = self._load_excel_data(effective_sheet_name, nrows=nrows)
            elif file_lower.endswith('.csv'):
                 # --- Pass nrows to helper ---
                df = self._load_csv_data(nrows=nrows)
            else:
                logger.error(f"Unsupported file format for loading data: {self.file_path}")
                return None

            # Store data and analyze columns only if loading full dataset
            if df is not None and nrows is None:
                 self.data = df
                 self._analyze_columns() # Analyze columns of the fully loaded data
                 logger.info(f"Successfully loaded {len(df)} rows.")
            elif df is not None and nrows is not None:
                 logger.info(f"Successfully loaded preview: {len(df)} rows.")
                 # Don't store preview in self.data, don't analyze columns based on preview
            else:
                 logger.error(f"Failed to load data from '{self.file_path}'.")


            return df # Return the loaded DataFrame (full or preview)

        except Exception as e:
            logger.error(f"Error loading data from '{self.file_path}': {e}", exc_info=True)
            return None

    # --- MODIFIED SIGNATURE ---
    def _load_excel_data(self, sheet_name: Union[str, int] = 0, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Load data from an Excel sheet with robust error handling."""
        if not self.file_path: return None

        # Determine preferred engine based on extension
        file_lower = self.file_path.lower()
        preferred_engine = None
        if file_lower.endswith('.xlsx') or file_lower.endswith('.xlsm'):
             preferred_engine = 'openpyxl'
        elif file_lower.endswith(('.xls', '.xlsb')):
             # Note: reading .xlsb might require pyxlsb engine installed
             # engine='pyxlsb' for .xlsb, engine='xlrd' for .xls
             # Pandas often selects correctly, but explicit is safer if needed.
             pass # Let pandas choose for .xls/.xlsb initially

        try:
            logger.debug(f"Reading Excel sheet '{sheet_name}' with engine='{preferred_engine or 'auto'}', nrows={nrows}")
            # --- Pass nrows to pandas ---
            df = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name,
                engine=preferred_engine,
                nrows=nrows # Pass nrows here
            )
            # Simple validation after load
            if df.empty:
                 logger.warning(f"Loaded empty DataFrame from sheet '{sheet_name}'.")
            return df
        except Exception as e:
            logger.warning(f"Initial Excel read failed for sheet '{sheet_name}': {e}. Trying alternatives.")
            # Add more specific fallbacks if needed (e.g., different engines)
            try:
                logger.debug(f"Retrying Excel read for sheet '{sheet_name}' without engine hint, nrows={nrows}")
                # --- Pass nrows to pandas ---
                df = pd.read_excel(self.file_path, sheet_name=sheet_name, nrows=nrows)
                if df.empty:
                     logger.warning(f"Loaded empty DataFrame from sheet '{sheet_name}' on retry.")
                return df
            except Exception as e_retry:
                logger.error(f"All Excel read attempts failed for sheet '{sheet_name}': {e_retry}", exc_info=True)
                return None

    # --- MODIFIED SIGNATURE ---
    def _load_csv_data(self, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Load data from a CSV file with encoding detection."""
        if not self.file_path: return None

        encodings_to_try = ['utf-8', 'latin1', 'cp1252']
        for encoding in encodings_to_try:
            try:
                logger.debug(f"Attempting CSV read with encoding='{encoding}', nrows={nrows}")
                # --- Pass nrows to pandas ---
                df = pd.read_csv(
                    self.file_path,
                    encoding=encoding,
                    low_memory=False,
                    nrows=nrows # Pass nrows here
                )
                logger.info(f"Successfully read CSV with encoding='{encoding}'.")
                if df.empty:
                     logger.warning("Loaded empty DataFrame from CSV.")
                return df
            except UnicodeDecodeError:
                logger.debug(f"Encoding {encoding} failed, trying next.")
                continue # Try next encoding
            except Exception as e:
                logger.warning(f"Error reading CSV with encoding {encoding}: {e}")
                # Don't retry generic errors immediately, might be format issue
                break # Stop trying encodings if another error occurs

        # If all encodings failed, try more flexible options (last resort)
        try:
             logger.warning("Standard CSV encodings failed, trying flexible options...")
             # --- Pass nrows to pandas ---
             df = pd.read_csv(
                 self.file_path,
                 sep=None, # Auto-detect separator
                 engine='python',
                 on_bad_lines='warn', # Log bad lines instead of skipping silently
                 nrows=nrows # Pass nrows here
             )
             logger.info("Successfully read CSV with flexible options.")
             if df.empty:
                 logger.warning("Loaded empty DataFrame from CSV with flexible options.")
             return df
        except Exception as e_flex:
            logger.error(f"All CSV reading attempts failed: {e_flex}", exc_info=True)
            return None


    def _analyze_columns(self) -> None:
        """Analyze columns of the fully loaded data to suggest mappings."""
        if self.data is None or self.data.empty:
            logger.warning("Cannot analyze columns: No data loaded.")
            return

        logger.debug("Analyzing columns for suggestions...")
        self.column_info = {
            'numeric_columns': [],
            'text_columns': [],
            'date_columns': [],
            'suggested_depth_column': None,
            'suggested_kp_column': None,
            'suggested_position_column': None,
            'suggested_lat_column': None,
            'suggested_lon_column': None,
            'suggested_easting_column': None,
            'suggested_northing_column': None,
        }

        # Define keywords for suggestions (lowercase)
        depth_kws = ['dol', 'depth', 'doc', 'burial']
        kp_kws = ['kp', 'chainage', 'meterage']
        pos_kws = ['pos', 'distance', 'seq', 'sequence'] # Generic position
        lat_kws = ['lat', 'latitude']
        lon_kws = ['lon', 'long', 'longitude']
        east_kws = ['east', 'easting', 'x']
        north_kws = ['north', 'northing', 'y']


        for col in self.data.columns:
            col_str = str(col) # Ensure it's a string
            col_lower = col_str.lower()

            # Determine type (simplistic check)
            try:
                numeric_series = pd.to_numeric(self.data[col_str], errors='coerce')
                non_null_count = numeric_series.count()
                total_count = len(self.data[col_str])
                numeric_ratio = (non_null_count / total_count) if total_count > 0 else 0

                if numeric_ratio > 0.7: # Heuristic: Mostly numeric
                    self.column_info['numeric_columns'].append(col_str)
                    # Check for suggestions ONLY if mostly numeric
                    if not self.column_info['suggested_depth_column'] and any(kw in col_lower for kw in depth_kws):
                         self.column_info['suggested_depth_column'] = col_str
                    elif not self.column_info['suggested_kp_column'] and any(kw in col_lower for kw in kp_kws):
                         self.column_info['suggested_kp_column'] = col_str
                    elif not self.column_info['suggested_position_column'] and any(kw in col_lower for kw in pos_kws):
                         self.column_info['suggested_position_column'] = col_str
                    elif not self.column_info['suggested_lat_column'] and any(kw in col_lower for kw in lat_kws):
                         self.column_info['suggested_lat_column'] = col_str
                    elif not self.column_info['suggested_lon_column'] and any(kw in col_lower for kw in lon_kws):
                         self.column_info['suggested_lon_column'] = col_str
                    elif not self.column_info['suggested_easting_column'] and any(kw in col_lower for kw in east_kws):
                         self.column_info['suggested_easting_column'] = col_str
                    elif not self.column_info['suggested_northing_column'] and any(kw in col_lower for kw in north_kws):
                         self.column_info['suggested_northing_column'] = col_str

                else: # Try datetime or fallback to text
                    try:
                         # Attempt datetime conversion on a sample for performance
                         pd.to_datetime(self.data[col_str].dropna().iloc[:100], errors='raise')
                         self.column_info['date_columns'].append(col_str)
                    except (ValueError, TypeError, OverflowError):
                         self.column_info['text_columns'].append(col_str)
            except Exception: # Catch any other error during type check
                 logger.warning(f"Could not reliably determine type for column '{col_str}', classifying as text.")
                 self.column_info['text_columns'].append(col_str)


        log_parts = [f"{len(self.column_info['numeric_columns'])} numeric",
                     f"{len(self.column_info['text_columns'])} text",
                     f"{len(self.column_info['date_columns'])} date"]
        logger.info(f"Column analysis complete: {', '.join(log_parts)} columns.")
        for key, value in self.column_info.items():
             if key.startswith('suggested_') and value:
                  logger.info(f"  {key.replace('_', ' ').title()}: {value}")


    def create_test_data(self, output_file: str, cable_length: int = 1000, target_depth: float = 1.5) -> bool:
        """
        Create test data file with simulated cable burial measurements.

        Args:
            output_file: Path where the test data should be saved.
            cable_length: Length of cable in meters.
            target_depth: Target burial depth in meters.

        Returns:
            bool: True if test data was created successfully, False otherwise.
        """
        if not output_file or not isinstance(output_file, str):
             logger.error("Invalid output file path provided for test data.")
             return False
        if cable_length <= 0:
             logger.error("Cable length must be positive.")
             return False

        try:
            logger.info(f"Creating test data: Length={cable_length}m, Target Depth={target_depth}m")

            # Create positions and KP values
            num_points = cable_length * 2 # Example: 2 points per meter
            positions = np.linspace(0, cable_length, num_points)
            kp_values = positions / 1000.0  # Convert to kilometer points

            # Generate random depths with normal distribution
            np.random.seed(42)  # For reproducibility
            mean_depth = target_depth * 1.1  # Average slightly > target
            std_dev = target_depth * 0.18    # More realistic std dev
            depths = np.random.normal(mean_depth, std_dev, num_points)
            # Ensure depths are physically plausible (e.g., not excessively deep)
            depths = np.clip(depths, -0.5, target_depth + 3.0) # Clip unreasonable values

            # --- Create test problem sections ---
            def create_section(start_kp, end_kp, depth_offset):
                 mask = (kp_values >= start_kp) & (kp_values <= end_kp)
                 depths[mask] = target_depth + depth_offset

            create_section(0.20, 0.25, -0.35) # Moderate deficit
            create_section(0.60, 0.63, -0.75) # Severe deficit (freespan maybe)
            create_section(0.80, 0.81, -0.15) # Minor deficit

            # --- Add some anomalies ---
            num_anomalies = max(5, int(num_points * 0.005)) # ~0.5% anomalies
            for _ in range(num_anomalies // 3): # Deep points
                 idx = np.random.randint(0, num_points)
                 depths[idx] = target_depth + 3.5 + np.random.rand() # Implausibly deep
            for _ in range(num_anomalies // 3): # Negative/surface points
                 idx = np.random.randint(0, num_points)
                 depths[idx] = np.random.uniform(-0.5, 0.05) # Error or exposed
            for _ in range(num_anomalies // 3): # Spikes
                 idx = np.random.randint(1, num_points - 1)
                 # Make spike relative to neighbours
                 spike_val = (depths[idx-1] + depths[idx+1]) / 2 + np.random.choice([-1, 1]) * 1.0
                 depths[idx] = np.clip(spike_val, -0.5, target_depth + 3.0)


            # Create the DataFrame
            test_data = pd.DataFrame({
                'KP': kp_values,
                'DepthOfBurial': depths # Use a more descriptive name
                # Add other potential columns if needed for testing (e.g., position quality)
            })
            # Round data for realism
            test_data['KP'] = test_data['KP'].round(3)
            test_data['DepthOfBurial'] = test_data['DepthOfBurial'].round(2)

            # Save to file
            file_lower = output_file.lower()
            if file_lower.endswith('.csv'):
                test_data.to_csv(output_file, index=False)
            elif file_lower.endswith('.xlsx'):
                test_data.to_excel(output_file, index=False, engine='openpyxl')
            else:
                 logger.error(f"Unsupported output file format: {output_file}. Use .csv or .xlsx.")
                 return False

            logger.info(f"Test data created successfully: '{output_file}'")

            # Automatically set this as the current file in the loader
            # self.set_file_path(output_file) # This reads info again
            # self.data = test_data # Store generated data
            # self._analyze_columns() # Analyze generated columns

            return True

        except Exception as e:
            logger.error(f"Failed to create test data: {e}", exc_info=True)
            return False

    # --- Methods below likely don't need nrows ---

    def get_preview(self, max_rows: int = 5) -> Optional[pd.DataFrame]:
        """Get a preview of the fully loaded data."""
        if self.data is None or self.data.empty:
            # Maybe try loading a preview if full data isn't loaded?
            # preview_df = self.load_data(nrows=max_rows)
            # return preview_df
            logger.warning("No full data loaded to get preview from.")
            return None
        return self.data.head(max_rows)

    def get_statistics(self) -> Dict:
        """Get basic statistics about the fully loaded data."""
        if self.data is None or self.data.empty:
            logger.warning("No full data loaded to get statistics from.")
            return {}

        stats: Dict[str, Any] = {
            'row_count': len(self.data),
            'column_count': len(self.data.columns),
            'columns': list(self.data.columns),
            'memory_usage': f"{self.data.memory_usage(deep=True).sum() / (1024*1024):.2f} MB",
            'missing_values_per_column': {},
            'numeric_stats': {}
        }

        # Calculate missing values
        missing = self.data.isnull().sum()
        stats['missing_values_per_column'] = missing[missing > 0].to_dict()

        # Add basic statistics for numeric columns identified during analysis
        numeric_cols = self.column_info.get('numeric_columns', [])
        if not numeric_cols and not self.column_info: # If columns weren't analyzed, try now
            self._analyze_columns()
            numeric_cols = self.column_info.get('numeric_columns', [])

        for col in numeric_cols:
            if col in self.data.columns: # Ensure column still exists
                try:
                    # Use describe() for efficiency
                    desc = self.data[col].describe()
                    col_stats = {
                        'count': int(desc.get('count', 0)),
                        'mean': float(desc.get('mean', np.nan)),
                        'std': float(desc.get('std', np.nan)),
                        'min': float(desc.get('min', np.nan)),
                        '25%': float(desc.get('25%', np.nan)),
                        '50%': float(desc.get('50%', np.nan)),
                        '75%': float(desc.get('75%', np.nan)),
                        'max': float(desc.get('max', np.nan)),
                    }
                    # Clean up NaN values if needed, although describe handles it
                    stats['numeric_stats'][col] = {k: v for k, v in col_stats.items() if pd.notna(v)}
                except Exception as e_stat:
                    logger.warning(f"Could not calculate stats for numeric column '{col}': {e_stat}")

        return stats