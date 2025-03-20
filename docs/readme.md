# CBATool - Cable Burial Analysis Tool v2.0

## Overview

CBATool (Cable Burial Analysis Tool) is a comprehensive Python application designed for analyzing cable burial depth data and position quality. The tool enables users to identify non-compliant cable burial sections, detect anomalies in measurement data, and generate interactive visualizations and detailed reports for better decision-making in submarine cable installation and maintenance.

## Key Features

- **Data Loading and Preprocessing**
  - Robust loading of Excel and CSV files with smart column detection
  - Support for various data formats and column layouts
  - Automatic handling of missing or corrupted data

- **Depth Analysis**
  - Identification of physically impossible values, sudden changes, and statistical outliers
  - Compliance checking against target burial depth requirements
  - Problem section identification and categorization by severity

- **Position Analysis**
  - KP (kilometer point) continuity analysis to detect jumps, reversals, and duplicates
  - Cross-track deviation assessment with configurable thresholds
  - Support for both Latitude/Longitude and Easting/Northing coordinate systems
  - Position quality scoring and visualization

- **Interactive Visualization**
  - HTML-based interactive plots for depth and position data
  - Color-coded problem section highlighting
  - Segmented visualization support for large datasets
  - Anomaly markers with detailed tooltips

- **Comprehensive Reporting**
  - Excel workbooks with multiple analysis sheets
  - PDF summary reports with key findings and recommendations
  - Customizable report formats and templates

- **Configuration Management**
  - Save and load analysis configurations
  - Predefined templates for different analysis scenarios
  - User-accessible configuration storage

## Project Structure

```
cbatool/
│
├── __init__.py                # Package initialization
├── __main__.py                # Main application entry point
├── core/                      # Core functionality
│   ├── __init__.py
│   ├── data_loader.py         # DataLoader class
│   ├── base_analyzer.py       # BaseAnalyzer abstract class
│   ├── depth_analyzer.py      # DepthAnalyzer class
│   ├── position_analyzer.py   # PositionAnalyzer class
│   ├── visualizer.py          # Visualizer class
│   └── position_visualizer.py # Position visualization functions
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── app.py                 # Main application class
│   ├── widgets.py             # Custom widgets
│   └── dialogs.py             # Custom dialog boxes
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── error_handling.py      # Error handling utilities
│   ├── file_operations.py     # File operation utilities
│   ├── constants.py           # Constants and configurations
│   ├── config_manager.py      # Configuration management
│   └── report_generator.py    # Report generation utilities
└── tests/                     # Unit tests
    ├── __init__.py
    └── test_core.py           # Tests for core functionality
```

## Requirements

- Python 3.7 or higher
- Required packages:
  - pandas
  - numpy
  - plotly
  - openpyxl (for Excel file handling)
  - reportlab (for PDF report generation)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/username/cbatool.git
   cd cbatool
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python -m cbatool
   ```

## Usage

### Basic Workflow

1. **Load Data File**
   - Click "File" → "Open Data File..." to select a CSV or Excel file
   - The application will automatically detect columns and suggest mappings

2. **Configure Analysis Parameters**
   - Set target burial depth (typically 1.5m)
   - Configure maximum trenching depth
   - Select appropriate columns for depth, KP, position, and coordinates
   - Adjust additional parameters as needed

3. **Run Analysis**
   - Click "Run Depth Analysis" for depth compliance analysis
   - Click "Run Position Analysis" for position quality analysis
   - Click "Run Complete Analysis" for comprehensive assessment

4. **View Results**
   - Interactive visualization will be generated
   - Problem sections report will be created
   - Anomaly detection report will be available
   - Option to view PDF summary or detailed Excel reports

### Configuration Management

- Use "Configuration" → "Save Configuration..." to save current settings
- Use "Configuration" → "Load Configuration..." to load saved profiles
- Use "Configuration" → "Manage Configurations..." for profile management
- Default configurations available for standard scenarios

### Analysis Output

- Interactive HTML visualizations will be saved to the output directory
- Excel reports will provide detailed data on problem sections and anomalies
- PDF summary reports provide key findings and recommendations

## Development Principles

The CBATool project follows these core development principles:

- **DRY** (Don't Repeat Yourself): Avoiding code duplication
- **KISS** (Keep It Simple, Stupid): Favoring simple solutions over complex ones
- **YAGNI** (You Aren't Gonna Need It): Implementing only what is needed
- **SOLID** Principles: Following object-oriented design principles

## Git Workflow

When contributing to this project, please follow the established git workflow:

1. Create feature branches from develop (`feature/descriptive-name`)
2. Make small, focused changes with descriptive commits
3. Keep feature branches updated with develop
4. Complete features before starting new ones
5. Use pull requests to merge back to develop

## Contributing

Contributions to CBATool are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch following our naming convention
3. Make your changes following the development principles
4. Add or update tests as necessary
5. Submit a pull request with a detailed description of changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Thomas Downs - Original author and maintainer

For more information, please refer to the detailed documentation in the `docs/` directory.
