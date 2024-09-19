import numpy as np
import matplotlib.pyplot as plt
from fanutils import FanCurve

def simulate_fan_curve(profile_file, temp_range):
    """
    Simulates the fan curve by calculating the fan RPM over a range of temperatures.
    
    Args:
        profile_file (str): Path to the JSON profile file.
        temp_range (np.array): Array of temperatures to simulate.
        
    Returns:
        np.array: Array of fan RPM values corresponding to the temperatures.
    """
    fan_curve = FanCurve(profile_file)
    rpm_values = [fan_curve.getFanRpm(temp) for temp in temp_range]
    return rpm_values

def plot_all_fan_curves(temp_range, profiles):
    """
    Plots multiple fan RPM vs. temperature curves on the same graph.
    
    Args:
        temp_range (np.array): Array of temperatures.
        profiles (list): List of profile JSON files to test.
    """
    plt.figure()

    for profile_file in profiles:
        # Extract profile name from file (for legend)
        profile_name = profile_file.split('.')[0].capitalize()

        # Simulate the fan curve for the given profile
        rpm_values = simulate_fan_curve(profile_file, temp_range)

        # Plot the curve on the same graph
        plt.plot(temp_range, rpm_values, label=profile_name)

    # Add titles and labels
    plt.title("Fan Curves Comparison")
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Fan RPM")
    plt.legend()
    plt.grid(True)
    
    # Show the graph once all profiles are plotted
    plt.show()

if __name__ == "__main__":
    # Define the temperature range to simulate (from 30°C to 100°C)
    temp_range = np.linspace(30, 100, 500)

    # Define the profiles to test
    profiles = ["default.curve.json", "gaming.curve.json", "silent.curve.json"]

    # Plot all fan curves on the same graph
    plot_all_fan_curves(temp_range, profiles)
