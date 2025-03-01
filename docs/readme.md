# Cable Burial Analysis Tool v2.0

A comprehensive tool for analyzing cable burial depth data, identifying non-compliant sections, and generating interactive visualizations.

## Overview

Cable Burial Analysis Tool (CBAtool) is designed to analyze submarine cable burial depth data to ensure compliance with required burial depths. The tool identifies sections where cable burial is insufficient, detects anomalies in the data, and provides interactive visualizations for better decision-making.

## Key Features

- **Data Loading**: Robust loading of Excel and CSV files with smart column detection
- **Anomaly Detection**: Identification of physically impossible values, sudden changes, and statistical outliers
- **Compliance Analysis**: Check burial depths against target requirements
- **Problem Section Identification**: Locate and categorize non-compliant sections
- **Interactive Visualization**: Create HTML-based interactive plots with Plotly
- **Reporting**: Generate Excel reports for problem sections and anomalies
- **Test Data Generation**: Create sample data for testing and demonstration

## Project Structure

```
cbatool/
│
├── __init__.py                # Package initialization
├── main.py                    # Main application entry point
├── core/                      # Core functionality
│   ├── __init__.py
│   ├── data_loader.py         # DataLoader class
│   ├── analyzer.py            # Analyzer class
│   └── visualizer.py          # Visualizer class
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── app.py                 # Main application class
│   ├── widgets.py             # Custom widgets
│   └── dialogs.py             # Custom dialog boxes
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── error_handling.py      # Error handling utilities
│   ├── file_operations.py     # File operation utilities
│   └── constants.py           # Constants and configurations
└── tests/                     # Unit tests
    ├── __init__.py
    ├── test_data_loader.py    # Tests for DataLoader
    ├── test_analyzer.py       # Tests for Analyzer
    └── test_visualizer.py     # Tests for Visualizer
```

## Requirements

- Python 3.7 or higher
- Required packages:
  - pandas
  - numpy
  - plotly
  - openpyxl (for Excel file handling)

## Installation

1. Clone the repository
   ```
   git clone https://github.com/username/cbatool.git
   cd cbatool
   ```

2. Install required packages
   ```
   pip install -r requirements.txt
   ```

3. Run the application
   ```
   python main.py
   ```

## Usage

1. **Load Data**: Use the "Browse" button to select an Excel or CSV file containing cable burial data
2. **Configure Settings**: Set target depth, maximum depth, and select appropriate columns
3. **Run Analysis**: Click "Run Analysis" to process the data
4. **View Results**: Examine the interactive visualization and reports

## Data Format

The tool works with tabular data containing at least the following:

- A depth column with burial depth measurements
- Optionally, a KP (kilometer point) column for position referencing
- Optionally, other position-related columns

## Visualization Features

- Color-coded sections based on compliance severity
- Anomaly markers with detailed tooltips
- Interactive zoom and pan capabilities
- Hoverable data points with measurement details
- Segmented display for large datasets
- Exportable as HTML files viewable in any modern browser

## Report Generation

The tool generates several output files:

1. **Interactive Visualization** (.html): A web-based interactive plot
2. **Problem Sections Report** (.xlsx): Detailed information about non-compliant sections
3. **Anomaly Report** (.xlsx): List of potential anomalies in the data

## New Features in v2.0

Version 2.0 of CBAtool includes several improvements over the original version:

- **Class-Based Architecture**: Modular design with separation of concerns
- **Improved Error Handling**: Comprehensive error handling and custom exceptions
- **Memory Optimizations**: Better handling of large datasets
- **Enhanced Visualization**: Segmented visualization for better performance with large datasets
- **Dark Mode**: User interface theme options
- **Thread-Based Processing**: Background processing for improved UI responsiveness
- **Enhanced Analysis**: More detailed anomaly detection and classification

## Future Enhancements

Planned enhancements for future versions include:

- Support for TDOL & ADOL CBRA values
- Improved handling of KP gaps and disjointed datasets
- Additional export format options
- Batch processing capabilities
- Comprehensive documentation and user manual
- Automated testing suite

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Thomas Downs - Original author and maintainer
- Claude 3.7 Sonnet & 3.5 Haiku - AI assistance for development

## Contact

For questions or support, please contact the project maintainer.