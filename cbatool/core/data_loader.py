"""
DataLoader module for CBAtool v2.0.

This module contains the DataLoader class responsible for loading data from various
file formats, with a focus on Excel files containing cable burial data.
"""

import os
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, List, Union, Tuple

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
        self.file_path = file_path
        self.data = None
        self.sheet_names = []
        self.column_info = {}
        
        # Load data if file path is provided
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
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        self.file_path = file_path
        return self._read_file_info()
    
    def _read_file_info(self) -> bool:
        """
        Read basic information from the file (sheet names, etc.).
        
        Returns:
            bool: True if file information was loaded successfully, False otherwise.
        """
        try:
            # Try to get sheet names
            if self.file_path.lower().endswith(('.xlsx', '.xls')):
                excel = pd.ExcelFile(self.file_path)
                self.sheet_names = excel.sheet_names
                logger.info(f"Found sheets: {self.sheet_names}")
                return True
            # Add support for CSV files
            elif self.file_path.lower().endswith('.csv'):
                self.sheet_names = ['Sheet1']  # Default name for CSV
                logger.info(f"CSV file detected, using default sheet name")
                return True
            else:
                logger.warning(f"Unsupported file format: {self.file_path}")
                return False
        except Exception as e:
            logger.error(f"Error reading file information: {str(e)}")
            return False
    
    def load_data(self, sheet_name: Union[str, int] = 0, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Load data from the specified file.
        
        Args:
            sheet_name: Name or index of the sheet to load.
            nrows: Number of rows to read (None reads all rows).
            
        Returns:
            DataFrame or None if loading failed.
        """
        if not self.file_path:
            logger.error("No file path set")
            return None
            
        logger.info(f"Loading data from {self.file_path}, sheet: {sheet_name}")
        
        try:
            # Handle different file types
            if self.file_path.lower().endswith(('.xlsx', '.xls')):
                return self._load_excel_data(sheet_name, nrows)
            elif self.file_path.lower().endswith('.csv'):
                return self._load_csv_data(nrows)
            else:
                logger.error(f"Unsupported file format: {self.file_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return None
    
    def _load_excel_data(self, sheet_name: Union[str, int] = 0, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Load data from an Excel file with robust error handling.
        
        Args:
            sheet_name: Name or index of the sheet to load.
            nrows: Number of rows to read (None reads all rows).
            
        Returns:
            DataFrame or None if loading failed.
        """
        # First try with auto engine
        try:
            logger.info("Attempting to read with auto engine selection...")
            df = pd.read_excel(self.file_path, sheet_name=sheet_name, nrows=nrows)
            
            if not df.empty:
                logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
                self.data = df
                self._analyze_columns()
                return df
            else:
                logger.warning("Loaded DataFrame is empty, trying alternate methods...")
        except Exception as e:
            logger.warning(f"Auto engine failed: {str(e)}, trying specific engines...")
        
        # Try with explicit engines
        for engine in ['openpyxl', 'xlrd']:
            try:
                logger.info(f"Attempting with {engine} engine...")
                
                options = {
                    'sheet_name': sheet_name,
                    'nrows': nrows,
                    'engine': engine,
                }
                
                # Try with header=None for files with unusual headers
                if engine == 'openpyxl':
                    options['header'] = None
                
                df = pd.read_excel(self.file_path, **options)
                
                if not df.empty:
                    # Check if columns are numeric (no header)
                    if all(isinstance(col, int) for col in df.columns):
                        # First row might be header
                        df.columns = df.iloc[0]
                        df = df.drop(0).reset_index(drop=True)
                        logger.info("Set first row as header")
                        
                        # Check if we still have data after setting header
                        if df.empty:
                            logger.warning("DataFrame empty after setting header, reverting")
                            df = pd.read_excel(self.file_path, sheet_name=sheet_name, engine=engine)
                    
                    logger.info(f"Successfully loaded {len(df)} rows with {engine}")
                    self.data = df
                    self._analyze_columns()
                    return df
            except Exception as e:
                logger.warning(f"Failed with {engine}: {str(e)}")
        
        logger.error("All loading methods failed")
        return None
    
    def _load_csv_data(self, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Load data from a CSV file.
        
        Args:
            nrows: Number of rows to read (None reads all rows).
            
        Returns:
            DataFrame or None if loading failed.
        """
        try:
            # Try different parsing options
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    logger.info(f"Attempting to read CSV with {encoding} encoding...")
                    df = pd.read_csv(
                        self.file_path, 
                        nrows=nrows,
                        encoding=encoding,
                        low_memory=False  # Avoid mixed type inference warnings
                    )
                    
                    if not df.empty:
                        logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
                        self.data = df
                        self._analyze_columns()
                        return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed with {encoding}: {str(e)}")
            
            # If standard options fail, try with more flexible options
            logger.info("Trying CSV read with flexible options...")
            df = pd.read_csv(
                self.file_path,
                nrows=nrows,
                sep=None,  # Try to detect separator
                engine='python',  # More flexible engine
                on_bad_lines='skip'  # Skip lines with too many fields
            )
            
            if not df.empty:
                logger.info(f"Successfully loaded {len(df)} rows with flexible options")
                self.data = df
                self._analyze_columns()
                return df
            
            logger.error("All CSV loading methods failed")
            return None
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            return None
    
    def _analyze_columns(self) -> None:
        """Analyze columns to determine types and suggest column mappings."""
        if self.data is None or self.data.empty:
            return
            
        # Reset column info
        self.column_info = {
            'numeric_columns': [],
            'text_columns': [],
            'date_columns': [],
            'suggested_depth_column': None,
            'suggested_kp_column': None,
            'suggested_position_column': None
        }
        
        # Analyze each column
        for col in self.data.columns:
            # Try to convert to numeric
            numeric_series = pd.to_numeric(self.data[col], errors='coerce')
            
            # Determine percentage of non-null values after conversion
            if len(self.data) > 0:
                numeric_percentage = numeric_series.count() / len(self.data)
            else:
                numeric_percentage = 0
                
            # Check column type
            if numeric_percentage > 0.7:  # Over 70% numeric values
                self.column_info['numeric_columns'].append(col)
                
                # Check column name for keywords to suggest mapping
                col_lower = str(col).lower()
                
                # Check for depth column
                if any(term in col_lower for term in ['dol', 'depth', 'burial', 'burial depth']):
                    self.column_info['suggested_depth_column'] = col
                
                # Check for KP column
                elif 'kp' in col_lower:
                    self.column_info['suggested_kp_column'] = col
                
                # Check for position column
                elif any(term in col_lower for term in ['position', 'chainage', 'distance']):
                    self.column_info['suggested_position_column'] = col
            else:
                # Check if it might be a date column
                try:
                    pd.to_datetime(self.data[col], errors='raise')
                    self.column_info['date_columns'].append(col)
                except:
                    self.column_info['text_columns'].append(col)
        
        logger.info(f"Column analysis complete: {len(self.column_info['numeric_columns'])} numeric, "
                   f"{len(self.column_info['text_columns'])} text, "
                   f"{len(self.column_info['date_columns'])} date columns")
        
        # Log suggestions
        if self.column_info['suggested_depth_column']:
            logger.info(f"Suggested depth column: {self.column_info['suggested_depth_column']}")
        if self.column_info['suggested_kp_column']:
            logger.info(f"Suggested KP column: {self.column_info['suggested_kp_column']}")
        if self.column_info['suggested_position_column']:
            logger.info(f"Suggested position column: {self.column_info['suggested_position_column']}")
    
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
        try:
            logger.info(f"Creating test data with length {cable_length}m and target depth {target_depth}m")
            
            # Create positions and KP values
            positions = np.arange(0, cable_length)
            kp_values = positions / 1000.0  # Convert to kilometer points
            
            # Generate random depths with normal distribution
            np.random.seed(42)  # For reproducibility
            mean_depth = target_depth * 1.2  # Average is 20% more than target
            std_dev = target_depth * 0.15    # Standard deviation
            depths = np.random.normal(mean_depth, std_dev, cable_length)
            
            # Create test problem sections
            # 1. Moderate deficit section (30cm below target)
            section1_start = int(cable_length * 0.2)
            section1_end = int(cable_length * 0.25)
            depths[section1_start:section1_end] = target_depth - 0.3
            
            # 2. Severe deficit section (70cm below target)
            section2_start = int(cable_length * 0.6)
            section2_end = int(cable_length * 0.63)
            depths[section2_start:section2_end] = target_depth - 0.7
            
            # 3. Minor deficit section (10cm below target)
            section3_start = int(cable_length * 0.8)
            section3_end = int(cable_length * 0.81)
            depths[section3_start:section3_end] = target_depth - 0.1
            
            # Add some anomalies
            # 1. A few impossibly deep points
            for i in range(3):
                idx = np.random.randint(0, cable_length)
                depths[idx] = 5.0  # Much deeper than physically possible
            
            # 2. A few negative/zero depths (errors)
            for i in range(2):
                idx = np.random.randint(0, cable_length)
                depths[idx] = -0.1  # Negative depth (impossible)
            
            # 3. A few spikes (dramatic changes)
            for i in range(5):
                idx = np.random.randint(10, cable_length-10)
                depths[idx] = depths[idx-1] + 1.5  # Big jump
            
            # Create the DataFrame
            test_data = pd.DataFrame({
                'Position': positions,
                'KP': kp_values,
                'DOB': depths  # Depth of Burial
            })
            
            # Save to Excel or CSV based on file extension
            if output_file.lower().endswith('.csv'):
                test_data.to_csv(output_file, index=False)
            else:  # Default to Excel
                test_data.to_excel(output_file, index=False)
            
            logger.info(f"Test data created successfully at {output_file}")
            
            # Load the created data
            self.set_file_path(output_file)
            self.data = test_data
            self._analyze_columns()
            
            return True
        except Exception as e:
            logger.error(f"Failed to create test data: {str(e)}")
            return False
            
    def get_preview(self, max_rows: int = 5) -> Optional[pd.DataFrame]:
        """
        Get a preview of the loaded data.
        
        Args:
            max_rows: Maximum number of rows to return.
            
        Returns:
            DataFrame with preview data or None if no data is loaded.
        """
        if self.data is None or self.data.empty:
            return None
            
        return self.data.head(max_rows)
        
    def get_statistics(self) -> Dict:
        """
        Get basic statistics about the loaded data.
        
        Returns:
            Dictionary with statistics or empty dict if no data is loaded.
        """
        if self.data is None or self.data.empty:
            return {}
            
        stats = {
            'row_count': len(self.data),
            'column_count': len(self.data.columns),
            'columns': list(self.data.columns),
            'missing_values': self.data.isnull().sum().to_dict(),
            'numeric_stats': {}
        }
        
        # Add basic statistics for numeric columns
        for col in self.column_info['numeric_columns']:
            try:
                col_stats = {
                    'min': float(self.data[col].min()),
                    'max': float(self.data[col].max()),
                    'mean': float(self.data[col].mean()),
                    'std': float(self.data[col].std()),
                    'non_null_count': int(self.data[col].count())
                }
                stats['numeric_stats'][col] = col_stats
            except:
                # Skip if statistics calculation fails
                pass
                
        return stats
