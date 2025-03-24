# Cable Registry Management Specification

## Data Characteristics

### Status Values
```python
VALID_STATUSES = [
    "not installed",
    "installed", 
    "burial in progress", 
    "burial complete"
]
```

### Cable Type Inference
```python
def infer_cable_type(cable_id: str) -> str:
    """
    Infer cable type based on ID prefix
    
    Args:
        cable_id (str): Cable identifier
    
    Returns:
        str: Cable type ('Export', 'Inter-Array', or 'Unknown')
    """
    if cable_id.startswith('GM_EXP'):
        return 'Export'
    elif cable_id.startswith('GM_IAC'):
        return 'Inter-Array'
    else:
        return 'Unknown'
```

### Validation Logic
```python
import pandas as pd
from typing import List, Dict, Any

class CableRegistryValidator:
    @staticmethod
    def validate_cable_registry(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive validation for cable registry
        
        Args:
            df (pd.DataFrame): Input DataFrame
        
        Returns:
            Dict with validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for required columns
        required_columns = ['ID', 'Status']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            results['is_valid'] = False
            results['errors'].append(f"Missing columns: {missing_columns}")
        
        # Check for duplicate IDs
        duplicates = df[df.duplicated('ID')]
        if not duplicates.empty:
            results['is_valid'] = False
            results['errors'].append(f"Duplicate IDs found: {duplicates['ID'].tolist()}")
        
        # Validate status values
        invalid_statuses = df[~df['Status'].isin(VALID_STATUSES)]
        if not invalid_statuses.empty:
            results['is_valid'] = False
            results['errors'].append(f"Invalid status values: {invalid_statuses['Status'].tolist()}")
        
        # Add warnings for potential issues
        not_installed_cables = df[df['Status'] == 'not installed']
        if not not_installed_cables.empty:
            results['warnings'].append(
                f"Cables not installed: {not_installed_cables['ID'].tolist()}"
            )
        
        return results

class CableRegistry:
    def __init__(self, csv_path: str):
        """
        Initialize Cable Registry from CSV
        
        Args:
            csv_path (str): Path to cable registry CSV
        """
        self.df = pd.read_csv(csv_path)
        self.validation_results = CableRegistryValidator.validate_cable_registry(self.df)
    
    def get_cables_by_type(self, cable_type: str = None) -> pd.DataFrame:
        """
        Get cables filtered by type
        
        Args:
            cable_type (str, optional): Type of cable to filter
        
        Returns:
            DataFrame of cables
        """
        if cable_type:
            return self.df[
                self.df['ID'].apply(infer_cable_type) == cable_type
            ]
        return self.df
    
    def get_cables_by_status(self, status: str = None) -> pd.DataFrame:
        """
        Get cables filtered by status
        
        Args:
            status (str, optional): Status to filter
        
        Returns:
            DataFrame of cables
        """
        if status:
            return self.df[self.df['Status'] == status]
        return self.df
    
    def get_available_cables_for_analysis(self) -> List[str]:
        """
        Get cables available for analysis
        
        Returns:
            List of cable IDs ready for analysis
        """
        return self.df[
            self.df['Status'].isin(['installed', 'burial complete'])
        ]['ID'].tolist()

# UI Integration Example
def populate_cable_dropdown(registry: CableRegistry, dropdown: ttk.Combobox):
    """
    Populate dropdown with cables available for analysis
    
    Args:
        registry (CableRegistry): Cable registry
        dropdown (ttk.Combobox): Dropdown to populate
    """
    available_cables = registry.get_available_cables_for_analysis()
    dropdown['values'] = available_cables
```

## Key Features
1. Flexible type inference
2. Comprehensive validation
3. Status-based filtering
4. Easy integration with UI

## Workflow
1. Import CSV
2. Validate registry
3. Filter and select cables
4. Use in analysis workflow

Clarifying Questions:
1. Are these the exact status values used across all projects?
2. Do you want to support additional statuses in the future?
3. What additional metadata might be useful to track?
4. How do you want to handle cables with non-analysis-ready statuses?

Would you like me to elaborate on any aspect of this implementation?