"""
Test script for the standardized ReportGenerator.

This script demonstrates how to use the ReportGenerator with
different types of analysis results.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# Import the ReportGenerator class
from cbatool.utils.report_generator import ReportGenerator

# Create an output directory for reports
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "CBAtool_Reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_depth_report():
    """Test generating reports from depth analysis results."""
    print("\nTesting depth analysis report generation...")
    
    # Create sample depth analysis results
    depth_results = {
        'analysis_complete': True,
        'target_depth': 1.5,
        'compliance_percentage': 92.4,
        'depth_analysis': create_sample_depth_data(),
        'anomalies': create_sample_depth_anomalies(),
        'problem_sections': create_sample_depth_problem_sections(),
        'total_problem_length': 153.2,
        'section_count': 5
    }
    
    # Create the report generator
    report_config = {
        'project_name': 'Sample Cable Project',
        'client_name': 'Acme Cable Co.',
        'company_name': 'Cable Analysis Ltd.',
        'regulatory_requirements': 'Burial depth must meet minimum 1.5m for 90% of cable length.'
    }
    
    generator = ReportGenerator(OUTPUT_DIR, report_config)
    
    # Generate reports
    reports = generator.generate_reports(
        depth_results,
        visualization_path=os.path.join(OUTPUT_DIR, "depth_visualization.html"),
        analysis_type='depth'
    )
    
    # Print report paths
    print("Generated Reports:")
    for report_type, path in reports.items():
        if isinstance(path, str):
            print(f"  {report_type}: {path}")
        elif isinstance(path, dict):
            print(f"  {report_type}:")
            for sub_type, sub_path in path.items():
                print(f"    {sub_type}: {sub_path}")
    
    return generator, reports

def test_position_report():
    """Test generating reports from position analysis results."""
    print("\nTesting position analysis report generation...")
    
    # Create sample position analysis results
    position_results = {
        'analysis_complete': True,
        'position_analysis': create_sample_position_data(),
        'problem_sections': create_sample_position_problem_sections(),
        'summary': {
            'total_points': 4235,
            'kp_range': (0.0, 4.235),
            'kp_length': 4.235,
            'quality_counts': {
                'Good': 3820,
                'Suspect': 350,
                'Poor': 65
            },
            'anomalies': {
                'kp_jumps': 3,
                'kp_reversals': 1,
                'kp_duplicates': 12
            }
        }
    }
    
    # Create the report generator
    report_config = {
        'project_name': 'Sample Cable Project',
        'client_name': 'Acme Cable Co.',
        'company_name': 'Cable Analysis Ltd.',
        'regulatory_requirements': 'Position data must maintain continuous KP values.',
        'analysis_type': 'position'  # Set analysis type explicitly to avoid incorrect detection
    }
    
    generator = ReportGenerator(OUTPUT_DIR, report_config)
    
    # Generate reports
    reports = generator.generate_reports(
        position_results,
        visualization_path=os.path.join(OUTPUT_DIR, "position_visualization.html"),
        analysis_type='position'
    )
    
    # Print report paths
    print("Generated Reports:")
    for report_type, path in reports.items():
        if isinstance(path, str):
            print(f"  {report_type}: {path}")
        elif isinstance(path, dict):
            print(f"  {report_type}:")
            for sub_type, sub_path in path.items():
                print(f"    {sub_type}: {sub_path}")
    
    return generator, reports

def test_combined_report():
    """Test generating reports from combined analysis results."""
    print("\nTesting combined analysis report generation...")
    
    # Create sample combined analysis results
    combined_results = {
        'analysis_complete': True,
        'target_depth': 1.5,
        'compliance_percentage': 92.4,
        'depth_analysis': create_sample_depth_data(),
        'anomalies': create_sample_depth_anomalies(),
        'problem_sections': create_sample_depth_problem_sections(),
        'total_problem_length': 153.2,
        'section_count': 5,
        'position_analysis': {
            'summary': {
                'total_points': 4235,
                'kp_range': (0.0, 4.235),
                'kp_length': 4.235,
                'quality_counts': {
                    'Good': 3820,
                    'Suspect': 350,
                    'Poor': 65
                },
                'anomalies': {
                    'kp_jumps': 3,
                    'kp_reversals': 1,
                    'kp_duplicates': 12
                }
            }
        }
    }
    
    # Add position problem segments separately to avoid confusion with depth problem sections
    position_problem_sections = create_sample_position_problem_sections()
    if not position_problem_sections.empty:
        combined_results['position_analysis']['problem_sections'] = position_problem_sections
    
    # Create the report generator
    report_config = {
        'project_name': 'Sample Cable Project',
        'client_name': 'Acme Cable Co.',
        'company_name': 'Cable Analysis Ltd.',
        'regulatory_requirements': 'Burial depth must meet minimum 1.5m for 90% of cable length. Position data must maintain continuous KP values.'
    }
    
    generator = ReportGenerator(OUTPUT_DIR, report_config)
    
    # Generate reports
    reports = generator.generate_reports(
        combined_results,
        visualization_path=os.path.join(OUTPUT_DIR, "combined_visualization.html"),
        analysis_type='combined'
    )
    
    # Print report paths
    print("Generated Reports:")
    for report_type, path in reports.items():
        if isinstance(path, str):
            print(f"  {report_type}: {path}")
        elif isinstance(path, dict):
            print(f"  {report_type}:")
            for sub_type, sub_path in path.items():
                print(f"    {sub_type}: {sub_path}")
    
    return generator, reports

def test_temporal_comparison():
    """Test generating temporal comparison report."""
    print("\nTesting temporal comparison report generation...")
    
    # Create sample depth analysis results for current and previous analysis
    current_results = {
        'analysis_complete': True,
        'target_depth': 1.5,
        'compliance_percentage': 94.2,  # Improved from previous
        'depth_analysis': create_sample_depth_data(),
        'anomalies': create_sample_depth_anomalies(count=8),  # Reduced anomalies
        'problem_sections': create_sample_depth_problem_sections(count=4),  # One less problem section
        'total_problem_length': 130.5,  # Reduced problem length
        'section_count': 4,
        'analysis_type': 'depth',
        'timestamp': datetime.now()  # Use actual datetime object
    }
    
    previous_results = {
        'analysis_complete': True,
        'target_depth': 1.5,
        'compliance_percentage': 92.4,
        'depth_analysis': create_sample_depth_data(),
        'anomalies': create_sample_depth_anomalies(count=12),
        'problem_sections': create_sample_depth_problem_sections(count=5),
        'total_problem_length': 153.2,
        'section_count': 5,
        'analysis_type': 'depth',
        'timestamp': '2023-12-01 10:30'
    }
    
    # Create the report generator
    report_config = {
        'project_name': 'Sample Cable Project',
        'client_name': 'Acme Cable Co.',
        'company_name': 'Cable Analysis Ltd.'
    }
    
    generator = ReportGenerator(OUTPUT_DIR, report_config)
    
    # Generate comparison report
    comparison_path = generator.create_temporal_comparison_report(
        current_results,
        previous_results,
        'depth_comparison_report.xlsx'
    )
    
    print(f"Temporal comparison report created: {comparison_path}")
    
    return generator, comparison_path

def create_sample_position_data(num_points=100):
    """Create minimal sample position data."""
    np.random.seed(42)
    return pd.DataFrame({
        'KP': np.linspace(0, 10, num_points),
        'Is_KP_Jump': np.random.choice([False, True], num_points, p=[0.9, 0.1]),
        'Is_KP_Reversal': np.random.choice([False, True], num_points, p=[0.95, 0.05])
    })

def create_sample_position_problem_sections():
    """Create minimal sample problem segments."""
    return pd.DataFrame([
        {
            'Section_ID': 1,
            'Start_KP': 1.0, 
            'End_KP': 2.0, 
            'Length_KP': 1.0, 
            'Severity': 'Medium',
            'Has_KP_Jumps': True
        }
    ])

def create_sample_depth_data():
    """Create sample depth analysis data."""
    # Create sample data with 1000 points
    np.random.seed(42)  # For reproducibility
    
    # Generate positions and KP values
    positions = np.arange(0, 1000)
    kp_values = positions / 1000.0  # Convert to kilometer points
    
    # Generate random depths with normal distribution
    mean_depth = 1.8  # Average slightly above target
    std_dev = 0.3    # Standard deviation
    depths = np.random.normal(mean_depth, std_dev, 1000)
    
    # Add a few problem sections
    # 1. Moderate deficit section (30cm below target)
    section1_start = int(1000 * 0.2)
    section1_end = int(1000 * 0.25)
    depths[section1_start:section1_end] = 1.2  # Below target
    
    # 2. Severe deficit section (70cm below target)
    section2_start = int(1000 * 0.6)
    section2_end = int(1000 * 0.63)
    depths[section2_start:section2_end] = 0.8  # Well below target
    
    # Add a few anomalies
    depths[50] = 5.0  # Too deep
    depths[400] = -0.1  # Negative (impossible)
    depths[700] = depths[699] + 1.5  # Spike
    
    
    # Create the DataFrame
    df = pd.DataFrame({
        'Position': positions,
        'KP': kp_values,
        'DOB': depths,  # Depth of Burial
        'Meets_Target': depths >= 1.5,
        'Depth_Deficit': np.maximum(0, 1.5 - depths),
        'Target_Percentage': (depths / 1.5 * 100).round(1),
    })
    
    # Add anomaly flags
    df['Exceeds_Max_Depth'] = df['DOB'] > 3.0
    df['Below_Min_Depth'] = df['DOB'] < 0.0
    df['Depth_Change'] = df['DOB'].diff().abs()
    df['Is_Spike'] = df['Depth_Change'] > 0.5
    df['Is_Outlier'] = False  # Just a placeholder
    df.loc[50, 'Is_Outlier'] = True
    
    # Combined anomaly flag
    df['Is_Anomaly'] = (
        df['Exceeds_Max_Depth'] | 
        df['Below_Min_Depth'] | 
        df['Is_Spike'] | 
        df['Is_Outlier']
    )
    
    # Add anomaly type and severity
    df['Anomaly_Type'] = ""
    df['Anomaly_Severity'] = ""
    
    for idx in df[df['Is_Anomaly']].index:
        if df.loc[idx, 'Exceeds_Max_Depth']:
            df.loc[idx, 'Anomaly_Type'] = "Exceeds maximum trenching depth"
            df.loc[idx, 'Anomaly_Severity'] = "High"
        elif df.loc[idx, 'Below_Min_Depth']:
            df.loc[idx, 'Anomaly_Type'] = "Invalid depth (below minimum)"
            df.loc[idx, 'Anomaly_Severity'] = "High"
        elif df.loc[idx, 'Is_Spike']:
            df.loc[idx, 'Anomaly_Type'] = f"Sudden depth change ({df.loc[idx, 'Depth_Change']:.2f}m)"
            df.loc[idx, 'Anomaly_Severity'] = "Medium"
        elif df.loc[idx, 'Is_Outlier']:
            df.loc[idx, 'Anomaly_Type'] = "Statistical outlier"
            df.loc[idx, 'Anomaly_Severity'] = "Medium"
    
    return df

def create_sample_depth_problem_sections(count=5):
    """Create sample depth problem sections."""
    # Create problem sections with different severities
    np.random.seed(42)  # For reproducibility
    
    sections = []
    
    # Create problem sections with different start positions
    start_positions = np.linspace(0, 900, count)
    
    for i, start_pos in enumerate(start_positions):
        start_pos = int(start_pos)
        
        # Vary section length based on severity
        if i % 3 == 0:
            severity = "High"
            length = np.random.randint(40, 60)
            deficit = 0.6 + np.random.random() * 0.4  # 0.6-1.0
        elif i % 3 == 1:
            severity = "Medium"
            length = np.random.randint(20, 40)
            deficit = 0.3 + np.random.random() * 0.3  # 0.3-0.6
        else:
            severity = "Low"
            length = np.random.randint(10, 30)
            deficit = 0.1 + np.random.random() * 0.2  # 0.1-0.3
        
        end_pos = start_pos + length
        
        min_depth = 1.5 - deficit  # Adjusted depth based on deficit
        
        # Calculate KP values
        start_kp = start_pos / 1000.0
        end_kp = end_pos / 1000.0
        
        # Calculate minimum depth (target - deficit)
        min_depth = 1.5 - deficit
        
        sections.append({
            'Section_ID': i + 1,
            'Position_Type': 'Position',
            'Start_Position': start_pos,
            'End_Position': end_pos,
            'Start_KP': start_kp,
            'End_KP': end_kp,
            'Length': f"{end_pos - start_pos}m ({(end_kp - start_kp):.3f}km)",
            'Length_Meters': end_pos - start_pos,
            'Min_Depth': min_depth,
            'Max_Depth': min_depth + np.random.random() * 0.3,  # Slight variation
            'Avg_Depth': min_depth + 0.15,
            'Max_Deficit': deficit,
            'Target_Percentage': round(min_depth / 1.5 * 100, 1),
            'Severity': severity,
            'Point_Count': length,
            'Recommendation': 'Requires remedial burial' if severity == 'High' else (
                'Consider additional protection' if severity == 'Medium' else 'Monitor during maintenance'
            )
        })
    
    return pd.DataFrame(sections)

if __name__ == "__main__":
    print("Running test_report_generator.py...")
    
    # Run tests
    test_depth_report()
    test_position_report()
    test_combined_report()
    test_temporal_comparison()