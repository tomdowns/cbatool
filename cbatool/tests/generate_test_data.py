import pandas as pd
import numpy as np
import os

# Set seed for reproducibility
np.random.seed(42)

# Create a function to generate test data
def generate_test_data(output_filename="test_cable_anomalies.csv", 
                     cable_length=1000, 
                     target_depth=1.5):
    """
    Generate comprehensive test data with various depth and position anomalies.
    
    Args:
        output_filename: Name of the CSV file to be saved
        cable_length: Length of cable in data points
        target_depth: Target burial depth in meters
    """
    print(f"Generating test data with {cable_length} points and target depth {target_depth}m")
    
    # Get the current directory where the script is run
    output_file = os.path.join(os.getcwd(), output_filename)

    # Create base data
    positions = np.arange(0, cable_length)
    kp_values = positions / 1000.0  # Convert to kilometer points
    
    # Generate basic depth values with normal distribution
    mean_depth = target_depth * 1.2  # Average is 20% more than target
    std_dev = target_depth * 0.15    # Standard deviation
    depths = np.random.normal(mean_depth, std_dev, cable_length)
    
    # Generate position components
    easting = 500000 + np.cumsum(np.random.normal(0, 0.5, cable_length))
    northing = 6000000 + np.cumsum(np.random.normal(0, 0.5, cable_length))
    
    # Convert easting/northing to lat/lon (simplified conversion)
    lat = northing / 111111  # Approx conversion
    lon = easting / (111111 * np.cos(np.radians(lat)))
    
    # Calculate cross-track deviation (DCC)
    dcc = np.random.normal(0, 1, cable_length)
    
    # Create DataFrame with all components
    data = pd.DataFrame({
        'Position': positions,
        'KP': kp_values,
        'DOB': depths,
        'Easting': easting,
        'Northing': northing,
        'Latitude': lat,
        'Longitude': lon,
        'DCC': dcc
    })
    
    # Add depth anomalies
    deficit_sections = [(100, 150, -0.3), (400, 450, -0.7), (700, 750, -1.0)]
    for start, end, adjustment in deficit_sections:
        data.loc[start:end, 'DOB'] = target_depth + adjustment
    
    # Physically impossible depths
    impossible_depths = {50: -0.5, 200: -0.2, 350: 10.0, 550: 8.5}
    for idx, depth in impossible_depths.items():
        data.loc[idx, 'DOB'] = depth
    
    # Depth spikes
    spike_indices = [75, 225, 375, 625, 825]
    for idx in spike_indices:
        data.loc[idx, 'DOB'] = data.loc[idx-1, 'DOB'] + 2.0  # Spike up
        data.loc[idx+1, 'DOB'] = data.loc[idx-1, 'DOB'] - 1.5  # Spike down
    
    # KP anomalies
    kp_jumps = [170, 470, 770]
    kp_reversals = [280, 580, 880]
    kp_duplicates = [300, 600, 900]
    
    for idx in kp_jumps:
        data.loc[idx, 'KP'] = data.loc[idx-1, 'KP'] + 0.2
    for idx in kp_reversals:
        data.loc[idx, 'KP'] = data.loc[idx-1, 'KP'] - 0.05
    for idx in kp_duplicates:
        data.loc[idx, 'KP'] = data.loc[idx-1, 'KP']
    
    # Coordinate jumps
    coord_jumps = [320, 520, 920]
    for idx in coord_jumps:
        data.loc[idx, ['Easting', 'Northing', 'Latitude', 'Longitude']] += 100
    
    # DCC anomalies
    dcc_anomalies = [250, 450, 650, 850]
    for idx in dcc_anomalies:
        data.loc[idx, 'DCC'] = 20
        data.loc[idx+1, 'DCC'] = -20
    
    # Save to CSV
    data.to_csv(output_file, index=False)
    print(f"Test data with anomalies saved to {output_file}")
    
    return data

# Generate the test data
if __name__ == "__main__":
    generate_test_data()
