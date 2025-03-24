"""
Cable Registry Management for CBAtool v2.0.

This module handles the management of cable identifiers, including:
- Loading/saving cable registry data from CSV files
- Validation and type inference for cable identifiers
- Filtering capabilities by cable type and status
- Integration with the application configuration system
"""

import os
import csv
import json
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
CABLE_TYPES = ["EXC", "IAC"]  # Export Cable, Inter-Array Cable
CABLE_STATUSES = ["not installed", "installed", "burial in progress", "burial complete"]

class CableRegistry:
    """
    Manages cable identifiers and associated metadata for the CBAtool.
    
    Provides functionality for loading, validating, and filtering cable data
    from CSV files, as well as integrating with the application configuration.
    
    Attributes:
        cables (pd.DataFrame): DataFrame containing cable registry data
        config (Dict): Configuration dictionary for the cable registry
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CableRegistry with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.cables = pd.DataFrame(columns=['cable_id', 'type', 'status', 'metadata'])
        self.config = config or {}
        
        # Initialize from config if cable identifiers are provided
        if config and 'cableIdentifiers' in config:
            self._initialize_from_config(config)
            
    def _initialize_from_config(self, config: Dict[str, Any]) -> None:
        """
        Initialize registry from configuration dictionary.
        
        Args:
            config: Configuration dictionary containing cableIdentifiers
        """
        try:
            cable_data = []
            
            for type_entry in config.get('cableIdentifiers', []):
                cable_type = type_entry.get('type', '')
                
                if cable_type and cable_type in CABLE_TYPES:
                    for cable_id in type_entry.get('identifiers', []):
                        cable_data.append({
                            'cable_id': cable_id,
                            'type': cable_type,
                            'status': "not installed",  # Default status
                            'metadata': {}
                        })
                        
            if cable_data:
                self.cables = pd.DataFrame(cable_data)
                logger.info(f"Initialized {len(cable_data)} cables from configuration")
                
        except Exception as e:
            logger.error(f"Error initializing from config: {str(e)}")
            
    def load_from_csv(self, file_path: str, delimiter: str = ',') -> bool:
        """
        Load cable registry data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            delimiter: CSV delimiter character
            
        Returns:
            bool: True if loading was successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"CSV file not found: {file_path}")
                return False
                
            # Read CSV into DataFrame
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            # Validate required columns
            required_cols = ['cable_id']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Missing required columns in CSV: {', '.join(missing_cols)}")
                return False
                
            # Process and clean the data
            df = self._process_csv_data(df)
            
            # Store in registry
            self.cables = df
            logger.info(f"Loaded {len(df)} cables from {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading from CSV: {str(e)}")
            return False
            
    def _process_csv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process and clean CSV data, inferring types and validating entries.
        
        Args:
            df: DataFrame with raw CSV data
            
        Returns:
            Processed DataFrame with validated entries
        """
        # Make a copy to avoid modifying the input
        result = df.copy()
        
        # Map common column names to expected names
        column_mapping = {
            'ID': 'cable_id',
            'CableID': 'cable_id',
            'Cable ID': 'cable_id',
            'Cable_ID': 'cable_id',
            'Type': 'type',
            'CableType': 'type',
            'Status': 'status'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in result.columns:
                result.rename(columns={old_name: new_name}, inplace=True)
        
        # Ensure required columns exist
        if 'cable_id' not in result.columns:
            result['cable_id'] = ""
            
        if 'type' not in result.columns:
            # Infer cable type from ID if not provided
            result['type'] = result['cable_id'].apply(self._infer_cable_type)
            
        if 'status' not in result.columns:
            # Default status
            result['status'] = "not installed"
        else:
            # Validate status values
            result['status'] = result['status'].apply(
                lambda x: x if x in CABLE_STATUSES else "not installed"
            )
            
        # Ensure metadata column exists (for additional properties)
        if 'metadata' not in result.columns:
            result['metadata'] = [{}] * len(result)
            
        return result
        
    @staticmethod
    def create_cable_selector(parent, label_text="Cable ID:", 
                               on_select: Optional[Callable[[str], None]] = None,
                               config: Optional[Dict[str, Any]] = None):
        """
        Create a UI component for cable selection.
        
        Args:
            parent: Parent tkinter widget
            label_text: Text for the label
            on_select: Optional callback function when a cable is selected
            config: Optional configuration dictionary
            
        Returns:
            Frame containing the cable selection widgets
        """
        frame = ttk.Frame(parent)
        
        # Create label
        label = ttk.Label(frame, text=label_text)
        label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Create combobox for cable selection
        cable_var = tk.StringVar()
        cable_combo = ttk.Combobox(frame, textvariable=cable_var, state="readonly", width=20)
        cable_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Create registry instance
        registry = CableRegistry(config)
        
        # Populate combobox initially
        cable_combo['values'] = registry.get_cable_ids()
        
        # Create type and status filters
        filter_frame = ttk.LabelFrame(frame, text="Filters")
        filter_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Type filter
        type_label = ttk.Label(filter_frame, text="Type:")
        type_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(filter_frame, textvariable=type_var, state="readonly", width=10)
        type_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        type_combo['values'] = ["All"] + CABLE_TYPES
        
        # Status filter
        status_label = ttk.Label(filter_frame, text="Status:")
        status_label.grid(row=0, column=2, sticky="w", padx=5, pady=2)
        
        status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=status_var, state="readonly", width=15)
        status_combo.grid(row=0, column=3, sticky="w", padx=5, pady=2)
        status_combo['values'] = ["All"] + CABLE_STATUSES
        
        # Import/export buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        import_btn = ttk.Button(button_frame, text="Import CSV", 
                            command=lambda: CableRegistry._import_csv_dialog(registry, cable_combo))
        import_btn.pack(side="left", padx=5)
        
        export_btn = ttk.Button(button_frame, text="Export CSV", 
                            command=lambda: CableRegistry._export_csv_dialog(registry))
        export_btn.pack(side="left", padx=5)
        
        add_btn = ttk.Button(button_frame, text="Add Cable", 
                          command=lambda: CableRegistry._add_cable_dialog(registry, cable_combo))
        add_btn.pack(side="left", padx=5)
        
        # Update function for filters
        def update_cable_list(*args):
            cable_type = None if type_var.get() == "All" else type_var.get()
            status = None if status_var.get() == "All" else status_var.get()
            
            # Get filtered cable IDs
            cable_ids = registry.get_cable_ids(cable_type=cable_type, status=status)
            
            # Update combobox values
            cable_combo['values'] = cable_ids
            
            # Clear current selection if it's not in the filtered list
            if cable_var.get() and cable_var.get() not in cable_ids:
                cable_var.set("")
            
            # Disable export button if no cables
            if not cable_ids:
                export_btn.config(state="disabled")
            else:
                export_btn.config(state="normal")
        
        # Bind update function to filter changes
        type_var.trace("w", update_cable_list)
        status_var.trace("w", update_cable_list)
        
        # Bind selection callback if provided
        if on_select:
            def on_cable_selected(*args):
                selected_cable = cable_var.get()
                if selected_cable:
                    on_select(selected_cable)
            
            cable_var.trace("w", on_cable_selected)
        
        # Store references to widgets and variables
        frame.registry = registry
        frame.cable_var = cable_var
        frame.type_var = type_var
        frame.status_var = status_var
        frame.update_cable_list = update_cable_list
        
        return frame
    
    @staticmethod
    def _import_csv_dialog(registry, cable_combo):
        """
        Open a dialog to import a CSV file.
        
        Args:
            registry: CableRegistry instance
            cable_combo: Combobox to update after import
        """
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Import Cable Registry",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if file_path:
            # Load from CSV
            success = registry.load_from_csv(file_path)
            
            if success:
                # Update combobox values
                cable_combo['values'] = registry.get_cable_ids()
                messagebox.showinfo("Import Successful", 
                                f"Imported {len(registry.cables)} cables from {file_path}")
            else:
                messagebox.showerror("Import Failed", 
                                  "Failed to import cable registry. Check format and try again.")
    
    @staticmethod
    def _export_csv_dialog(registry):
        """
        Open a dialog to export the cable registry to a CSV file.
        
        Args:
            registry: CableRegistry instance
        """
        if registry.cables.empty:
            messagebox.showwarning("No Data", "Cable registry is empty. Nothing to export.")
            return
            
        # Open file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Cable Registry",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if file_path:
            # Save to CSV
            success = registry.save_to_csv(file_path)
            
            if success:
                messagebox.showinfo("Export Successful", 
                                f"Exported {len(registry.cables)} cables to {file_path}")
            else:
                messagebox.showerror("Export Failed", 
                                  "Failed to export cable registry.")
    
    @staticmethod
    def _add_cable_dialog(registry, cable_combo):
        """
        Open a dialog to add a new cable to the registry.
        
        Args:
            registry: CableRegistry instance
            cable_combo: Combobox to update after adding
        """
        # Create dialog
        dialog = tk.Toplevel()
        dialog.title("Add New Cable")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(cable_combo.winfo_toplevel())
        dialog.grab_set()
        
        # Center dialog on parent window
        parent = cable_combo.winfo_toplevel()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Create form
        ttk.Label(dialog, text="Cable ID:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        id_var = tk.StringVar()
        id_entry = ttk.Entry(dialog, textvariable=id_var, width=30)
        id_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        ttk.Label(dialog, text="Cable Type:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(dialog, textvariable=type_var, state="readonly", width=10)
        type_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        type_combo['values'] = CABLE_TYPES
        
        ttk.Label(dialog, text="Status:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        status_var = tk.StringVar(value="not installed")
        status_combo = ttk.Combobox(dialog, textvariable=status_var, state="readonly", width=15)
        status_combo.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        status_combo['values'] = CABLE_STATUSES
        
        # Add metadata section (simplified)
        ttk.Label(dialog, text="Description (optional):").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=30)
        desc_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        
        # Automatically infer type from ID when typed
        def infer_type(*args):
            cable_id = id_var.get()
            if cable_id and not type_var.get():
                inferred_type = registry._infer_cable_type(cable_id)
                if inferred_type:
                    type_var.set(inferred_type)
        
        id_var.trace("w", infer_type)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        def add_cable():
            cable_id = id_var.get().strip()
            cable_type = type_var.get()
            status = status_var.get()
            
            # Validate input
            if not cable_id:
                messagebox.showerror("Validation Error", "Cable ID is required.")
                return
                
            if not cable_type:
                messagebox.showerror("Validation Error", "Cable Type is required.")
                return
                
            # Create metadata
            metadata = {}
            if desc_var.get().strip():
                metadata['description'] = desc_var.get().strip()
            
            # Add to registry
            success = registry.add_cable(cable_id, cable_type, status, metadata)
            
            if success:
                messagebox.showinfo("Success", f"Added cable {cable_id} to registry.")
                
                # Update combobox values
                cable_combo['values'] = registry.get_cable_ids()
                
                # Close dialog
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"Failed to add cable {cable_id}. It may already exist.")
        
        ttk.Button(button_frame, text="Add", command=add_cable).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        
        # Set focus to ID entry
        id_entry.focus_set()
            
    def _infer_cable_type(self, cable_id: str) -> str:
        """
        Infer cable type from cable ID based on common prefixes.
        
        Args:
            cable_id: Cable identifier string
            
        Returns:
            Inferred cable type or empty string if cannot be determined
        """
        if not cable_id or not isinstance(cable_id, str):
            return ""
            
        cable_id = cable_id.upper()
        
        # Check for export cable patterns (common prefixes)
        export_prefixes = ["EXC", "EXP", "EX", "EC"]
        for prefix in export_prefixes:
            if cable_id.startswith(prefix):
                return "EXC"
                
        # Check for inter-array cable patterns
        interarray_prefixes = ["IAC", "IA", "IC", "INT"]
        for prefix in interarray_prefixes:
            if cable_id.startswith(prefix):
                return "IAC"
                
        # Special case handling
        if "EXPORT" in cable_id:
            return "EXC"
        if "ARRAY" in cable_id or "INTER" in cable_id:
            return "IAC"
            
        # Default to empty if unknown
        return ""
        
    def save_to_csv(self, file_path: str, delimiter: str = ',') -> bool:
        """
        Save the current cable registry to a CSV file.
        
        Args:
            file_path: Path where CSV file should be saved
            delimiter: CSV delimiter character
            
        Returns:
            bool: True if saving was successful, False otherwise
        """
        try:
            if self.cables.empty:
                logger.warning("No cables in registry to save")
                return False
                
            # Create a copy for export (handle metadata serialization)
            export_df = self.cables.copy()
            
            # Convert metadata dict to JSON string
            if 'metadata' in export_df.columns:
                export_df['metadata'] = export_df['metadata'].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else x
                )
                
            # Save to CSV
            export_df.to_csv(file_path, index=False, sep=delimiter)
            logger.info(f"Saved {len(export_df)} cables to {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return False
            
    def get_cables(self, cable_type: Optional[str] = None, 
                  status: Optional[str] = None) -> pd.DataFrame:
        """
        Get cables with optional filtering by type and status.
        
        Args:
            cable_type: Optional cable type to filter by
            status: Optional status to filter by
            
        Returns:
            DataFrame with filtered cables
        """
        if self.cables.empty:
            return pd.DataFrame()
            
        result = self.cables.copy()
        
        # Apply filters if specified
        if cable_type and cable_type in CABLE_TYPES:
            result = result[result['type'] == cable_type]
            
        if status and status in CABLE_STATUSES:
            result = result[result['status'] == status]
            
        return result
        
    def get_cable_types(self) -> List[str]:
        """
        Get list of available cable types in the registry.
        
        Returns:
            List of unique cable types
        """
        if 'type' in self.cables.columns and not self.cables.empty:
            return self.cables['type'].unique().tolist()
        return []
        
    def get_cable_statuses(self) -> List[str]:
        """
        Get list of available cable statuses in the registry.
        
        Returns:
            List of unique cable statuses
        """
        if 'status' in self.cables.columns and not self.cables.empty:
            return self.cables['status'].unique().tolist()
        return []
        
    def get_cable_ids(self, cable_type: Optional[str] = None, 
                     status: Optional[str] = None) -> List[str]:
        """
        Get list of cable IDs with optional filtering.
        
        Args:
            cable_type: Optional cable type to filter by
            status: Optional status to filter by
            
        Returns:
            List of cable IDs
        """
        filtered = self.get_cables(cable_type, status)
        
        if not filtered.empty and 'cable_id' in filtered.columns:
            return filtered['cable_id'].tolist()
        return []
        
    def add_cable(self, cable_id: str, cable_type: str = "", 
                 status: str = "not installed", 
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a new cable to the registry.
        
        Args:
            cable_id: Unique identifier for the cable
            cable_type: Type of cable ("EXC" or "IAC")
            status: Current status of the cable
            metadata: Optional metadata dictionary
            
        Returns:
            bool: True if cable was added successfully, False otherwise
        """
        try:
            # Validate input
            if not cable_id:
                logger.error("Cable ID cannot be empty")
                return False
                
            # Check if cable already exists
            if not self.cables.empty and 'cable_id' in self.cables.columns:
                if cable_id in self.cables['cable_id'].values:
                    logger.error(f"Cable ID '{cable_id}' already exists in registry")
                    return False
            
            # Infer type if not provided
            if not cable_type:
                cable_type = self._infer_cable_type(cable_id)
                
            # Validate status
            if status not in CABLE_STATUSES:
                status = "not installed"
                
            # Prepare metadata
            meta = metadata or {}
            
            # Create new cable entry
            new_cable = pd.DataFrame([{
                'cable_id': cable_id,
                'type': cable_type,
                'status': status,
                'metadata': meta
            }])
            
            # Add to registry
            self.cables = pd.concat([self.cables, new_cable], ignore_index=True)
            logger.info(f"Added cable {cable_id} to registry")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding cable: {str(e)}")
            return False
            
    def update_cable_status(self, cable_id: str, new_status: str) -> bool:
        """
        Update the status of a cable in the registry.
        
        Args:
            cable_id: Cable identifier
            new_status: New status value
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Validate status
            if new_status not in CABLE_STATUSES:
                logger.error(f"Invalid status: {new_status}")
                return False
                
            # Find cable in registry
            if self.cables.empty or 'cable_id' not in self.cables.columns:
                logger.error("Registry is empty or missing cable_id column")
                return False
                
            mask = self.cables['cable_id'] == cable_id
            if not mask.any():
                logger.error(f"Cable ID '{cable_id}' not found in registry")
                return False
                
            # Update status
            self.cables.loc[mask, 'status'] = new_status
            logger.info(f"Updated status of cable {cable_id} to {new_status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating cable status: {str(e)}")
            return False
            
    def validate_registry(self) -> Tuple[bool, List[str]]:
        """
        Validate the entire cable registry for consistency and completeness.
        
        Returns:
            Tuple: (is_valid, list_of_validation_issues)
        """
        issues = []
        
        try:
            if self.cables.empty:
                issues.append("Cable registry is empty")
                return False, issues
                
            # Check required columns
            required_cols = ['cable_id', 'type', 'status']
            missing_cols = [col for col in required_cols if col not in self.cables.columns]
            
            if missing_cols:
                issues.append(f"Missing required columns: {', '.join(missing_cols)}")
                return False, issues
                
            # Check for empty cable IDs
            if self.cables['cable_id'].isnull().any() or (self.cables['cable_id'] == "").any():
                issues.append("Some cable IDs are empty or null")
                
            # Check for duplicate cable IDs
            duplicates = self.cables['cable_id'].duplicated()
            if duplicates.any():
                duplicate_ids = self.cables.loc[duplicates, 'cable_id'].tolist()
                issues.append(f"Duplicate cable IDs: {', '.join(duplicate_ids)}")
                
            # Check for valid cable types
            invalid_types = ~self.cables['type'].isin(CABLE_TYPES) & (self.cables['type'] != "")
            if invalid_types.any():
                invalid_type_ids = self.cables.loc[invalid_types, 'cable_id'].tolist()
                issues.append(f"Invalid cable types for: {', '.join(invalid_type_ids)}")
                
            # Check for valid statuses
            invalid_statuses = ~self.cables['status'].isin(CABLE_STATUSES)
            if invalid_statuses.any():
                invalid_status_ids = self.cables.loc[invalid_statuses, 'cable_id'].tolist()
                issues.append(f"Invalid statuses for: {', '.join(invalid_status_ids)}")
                
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
            return False, issues

    def export_to_config(self) -> Dict[str, Any]:
        """
        Export current cable registry to configuration format.
        
        Returns:
            Dictionary suitable for including in application configuration
        """
        if self.cables.empty:
            return {'cableIdentifiers': []}
            
        result = {'cableIdentifiers': []}
        
        # Group by type
        for cable_type in self.get_cable_types():
            if cable_type in CABLE_TYPES:
                cable_ids = self.get_cable_ids(cable_type=cable_type)
                if cable_ids:
                    result['cableIdentifiers'].append({
                        'type': cable_type,
                        'identifiers': cable_ids
                    })
        
        return result
