import tkinter as tk
from tkinter import ttk, messagebox


import os
import sys
import subprocess, time

from fanutils import FanCurve, FanController, Fan

# Initialize fan controller and fan instance
fan_ctl = FanController()
fan0 = Fan(0, fan_ctl)  # Fan 0 (you can modify the fan ID as needed)

curve_enabled = False  # Flag to track if the curve is currently enabled

def update_fan_data():
    """
    Updates the fan data and temperature readings in the GUI in real-time.
    """
    try:
        # Get system data from FanController
        data = fan_ctl.getAllControllerData()
        hi_cpu_temp = round(fan_ctl.getHighestCpuTemp(data), 1)
        avg_gpu_temp = round(fan_ctl.getAverageGpuTemp(data), 1)
        actual_speed = round(fan0.getActualSpeed(fan_ctl.getFanData()), 0)
        target_speed = round(fan0.getTargetSpeed(fan_ctl.getFanData()), 0)
        boundaries = fan0.getSpeedBoundaries(fan_ctl.getFanData())
        
        # Calculate the maximum of CPU and GPU temperatures
        max_temp = round(max(hi_cpu_temp, avg_gpu_temp), 1)
        
        # Update the labels in the GUI
        cpu_temp_label.config(text=f"Highest CPU Temp: {hi_cpu_temp} °C")
        gpu_temp_label.config(text=f"Average GPU Temp: {avg_gpu_temp} °C")
        actual_speed_label.config(text=f"Fan 0 Actual Speed: {actual_speed} RPM")
        target_speed_label.config(text=f"Fan 0 Target Speed: {target_speed} RPM")
        boundaries_label.config(text=f"Fan 0 Speed Boundaries: {boundaries}")
        max_temp_label.config(text=f"Max(CPU, GPU) Temp: {max_temp} °C")

        # Repeat the update every 1 second
        window.after(1000, update_fan_data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to retrieve fan data: {e}")

def on_set_curve_button_click():
    """
    Sets the fan to manual mode and adjusts the speed based on the selected curve and max(CPU, GPU) temperature.
    """
    global curve_enabled
    try:
        # Disable manual fan speed input
        manual_speed_entry.config(state=tk.DISABLED)
        set_manual_speed_button.config(state=tk.DISABLED)
        
        # Get the selected profile from the dropdown
        selected_profile = profile_combobox.get()
        profile_file = f"{selected_profile.lower()}.curve.json"
        
        # Get the system temperature data
        data = fan_ctl.getAllControllerData()
        hi_cpu_temp = fan_ctl.getHighestCpuTemp(data)
        avg_gpu_temp = fan_ctl.getAverageGpuTemp(data)
        
        # Calculate the maximum of CPU and GPU temperatures
        max_temp = round(max(hi_cpu_temp, avg_gpu_temp), 1)
        
        # Load the fan curve from the selected profile
        fan_curve = FanCurve(profile_file)
        
        # Calculate the target RPM using the fan curve and the max temperature
        target_rpm = round(fan_curve.getFanRpm(max_temp), 0)
        
        # Switch to manual mode and set the calculated RPM
        if fan0.isFanInAuto(fan_ctl.getFanData()):
            fan0.changeFanMode(1)
        
        fan0.setFanSpeed(int(target_rpm))
        curve_enabled = True
        messagebox.showinfo("Fan Speed", f"Fan speed set to {target_rpm} RPM based on {selected_profile} curve.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to set fan speed using curve: {e}")
        

def on_stop_curve_button_click():
    """
    Stops the fan curve and switches back to auto mode.
    """
    global curve_enabled
    try:
        # Ensure the fan is in auto mode
        if not fan0.isFanInAuto(fan_ctl.getFanData()):
            fan0.changeFanMode(0)
            messagebox.showinfo("Fan Mode", "Fan has been set to auto mode.")
        
        # Re-enable manual fan speed input
        manual_speed_entry.config(state=tk.NORMAL)
        set_manual_speed_button.config(state=tk.NORMAL)
        curve_enabled = False

    except Exception as e:
        messagebox.showerror("Error", f"Failed to stop fan curve and set auto mode: {e}")

def on_set_manual_speed_click():
    """
    Sets the fan speed manually in manual mode (only if curve is disabled).
    """
    try:
        # Ensure the curve is not active
        if curve_enabled:
            messagebox.showerror("Error", "Curve is enabled. Stop the curve before setting manual speed.")
            return
        
        # Get the entered manual RPM
        manual_rpm = int(manual_speed_entry.get())
        
        # Switch to manual mode if necessary
        if fan0.isFanInAuto(fan_ctl.getFanData()):
            fan0.changeFanMode(1)
        
        # Set the manual RPM
        fan0.setFanSpeed(manual_rpm)
        messagebox.showinfo("Fan Speed", f"Fan speed manually set to {manual_rpm} RPM.")
        
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid RPM value.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to set manual fan speed: {e}")
        raise e

def on_closing():
    """
    Event handler for when the window is closed. It sets the fan back to auto mode before exiting.
    """
    try:
        # Ensure the fan is in auto mode before exiting
        if not fan0.isFanInAuto(fan_ctl.getFanData()):
            fan0.changeFanMode(0)
            messagebox.showinfo("Fan Mode", "Fan has been set to auto mode.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to set fan to auto mode: {e}")
    window.destroy()

# Set up the main tkinter window
window = tk.Tk()
window.title("Fan Curve and Control GUI")
window.geometry("400x700")

# Temperature and fan data labels
cpu_temp_label = tk.Label(window, text="Highest CPU Temp: N/A")
cpu_temp_label.pack(pady=5)

gpu_temp_label = tk.Label(window, text="Average GPU Temp: N/A")
gpu_temp_label.pack(pady=5)

actual_speed_label = tk.Label(window, text="Fan 0 Actual Speed: N/A")
actual_speed_label.pack(pady=5)

target_speed_label = tk.Label(window, text="Fan 0 Target Speed: N/A")
target_speed_label.pack(pady=5)

boundaries_label = tk.Label(window, text="Fan 0 Speed Boundaries: N/A")
boundaries_label.pack(pady=5)

max_temp_label = tk.Label(window, text="Max(CPU, GPU) Temp: N/A")
max_temp_label.pack(pady=5)

# Fan curve selection
profile_label = tk.Label(window, text="Select Fan Profile:")
profile_label.pack(pady=10)

profile_combobox = ttk.Combobox(window, values=["Default", "Gaming", "Silent"])
profile_combobox.set("Default")  # Set default profile
profile_combobox.pack(pady=5)

# Button to apply the selected curve to the fan
set_curve_button = tk.Button(window, text="Set Fan Speed Based on Curve", command=on_set_curve_button_click)
set_curve_button.pack(pady=20)

# Button to stop using the curve and go back to auto mode
stop_curve_button = tk.Button(window, text="Stop Curve and Set Auto Mode", command=on_stop_curve_button_click)
stop_curve_button.pack(pady=20)

# Manual fan speed control section
manual_speed_label = tk.Label(window, text="Set Fan Speed Manually (RPM):")
manual_speed_label.pack(pady=5)

manual_speed_entry = tk.Entry(window)
manual_speed_entry.insert(0, "2000") 
manual_speed_entry.pack(pady=5)

set_manual_speed_button = tk.Button(window, text="Set Manual Fan Speed", command=on_set_manual_speed_click)
set_manual_speed_button.pack(pady=20)

# Start updating the fan data
update_fan_data()

# Handle window close event (set fan to auto mode when quitting)
window.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI event loop
window.mainloop()