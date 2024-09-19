import rumps
import os
import sys
import subprocess, time

from fanutils import FanCurve, FanController, Fan

# Initialize fan controller and fan instance
fan_ctl = FanController()
fan0 = Fan(0, fan_ctl)  # Fan 0 (you can modify the fan ID as needed)

curve_enabled = False  # Flag to track if the curve is currently enabled

class FanControlApp(rumps.App):
    def __init__(self):
        super(FanControlApp, self).__init__("Fan Control")
        self.curves = ["Default", "Gaming", "Silent"]  # Available fan curves
        self.selected_curve = "Default"  # Default curve selection

        # Create fan curve menu
        set_fan_curve_menu = rumps.MenuItem("Set Fan Curve")
        for curve in self.curves:
            set_fan_curve_menu.add(rumps.MenuItem(curve))

        # Create manual fan speed menu
        manual_fan_speed_menu = rumps.MenuItem("Manual Fan Speed")
        for rpm in ["2000 RPM", "3000 RPM", "4000 RPM"]:
            manual_fan_speed_menu.add(rumps.MenuItem(rpm))

        # Add menu items
        self.menu = [
            "Show Fan and Temp Data",
            set_fan_curve_menu,  # Submenu for fan curves
            "Set Fan Speed Based on Curve",
            "Stop Curve and Set Auto Mode",
            manual_fan_speed_menu,  # Submenu for manual fan speeds
            "Set Custom Fan Speed...",
        ]
        self.update_fan_data()

    def update_fan_data(self, _=None):
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
            
            # Update menubar title to show current status
            self.title = f"CPU: {hi_cpu_temp}°C, GPU: {avg_gpu_temp}°C, Fan: {actual_speed} RPM"

        except Exception as e:
            rumps.notification("Error", "Fan Control", f"Failed to retrieve fan data: {e}")
        
        # Schedule next update in 1 second
        rumps.timer(1)(self.update_fan_data)

    @rumps.clicked("Show Fan and Temp Data")
    def show_fan_data(self, _):
        try:
            data = fan_ctl.getAllControllerData()
            hi_cpu_temp = round(fan_ctl.getHighestCpuTemp(data), 1)
            avg_gpu_temp = round(fan_ctl.getAverageGpuTemp(data), 1)
            actual_speed = round(fan0.getActualSpeed(fan_ctl.getFanData()), 0)
            target_speed = round(fan0.getTargetSpeed(fan_ctl.getFanData()), 0)
            boundaries = fan0.getSpeedBoundaries(fan_ctl.getFanData())
            
            max_temp = round(max(hi_cpu_temp, avg_gpu_temp), 1)
            
            rumps.notification("Fan and Temp Data", 
                               "Fan Control",
                               f"CPU Temp: {hi_cpu_temp}°C\nGPU Temp: {avg_gpu_temp}°C\nFan Speed: {actual_speed} RPM\nBoundaries: {boundaries}\nMax Temp: {max_temp}°C")
        
        except Exception as e:
            rumps.notification("Error", "Fan Control", f"Failed to show fan data: {e}")
    
    @rumps.clicked("Set Fan Speed Based on Curve")
    def on_set_curve_button_click(self, _):
        global curve_enabled
        try:
            # Get the system temperature data
            data = fan_ctl.getAllControllerData()
            hi_cpu_temp = fan_ctl.getHighestCpuTemp(data)
            avg_gpu_temp = fan_ctl.getAverageGpuTemp(data)
            
            max_temp = round(max(hi_cpu_temp, avg_gpu_temp), 1)
            
            # Load the fan curve from the selected profile
            profile_file = f"{self.selected_curve.lower()}.curve.json"
            fan_curve = FanCurve(profile_file)
            
            # Calculate the target RPM using the fan curve and the max temperature
            target_rpm = round(fan_curve.getFanRpm(max_temp), 0)
            
            # Switch to manual mode and set the calculated RPM
            if fan0.isFanInAuto(fan_ctl.getFanData()):
                fan0.changeFanMode(1)
            
            fan0.setFanSpeed(int(target_rpm))
            curve_enabled = True
            rumps.notification("Fan Speed", "Fan Control", f"Fan speed set to {target_rpm} RPM based on {self.selected_curve} curve.")
        
        except Exception as e:
            rumps.notification("Error", "Fan Control", f"Failed to set fan speed using curve: {e}")

    @rumps.clicked("Stop Curve and Set Auto Mode")
    def on_stop_curve_button_click(self, _):
        global curve_enabled
        try:
            # Ensure the fan is in auto mode
            if not fan0.isFanInAuto(fan_ctl.getFanData()):
                fan0.changeFanMode(0)
                rumps.notification("Fan Mode", "Fan Control", "Fan has been set to auto mode.")
            
            curve_enabled = False

        except Exception as e:
            rumps.notification("Error", "Fan Control", f"Failed to stop fan curve and set auto mode: {e}")

    @rumps.clicked("Set Custom Fan Speed...")
    def on_set_custom_speed_click(self, _):
        response = rumps.Window(
            title="Set Custom Fan Speed",
            message="Enter the desired RPM:",
            default_text="2000",
            dimensions=(200, 40)
        ).run()

        # Check if the input is empty or canceled
        if response.text.strip() == "":
            rumps.notification("Error", "Fan Control", "No RPM entered. Please enter a valid RPM.")
            return

        try:
            manual_rpm = int(response.text.strip())  # Ensure the input is converted to an integer

            if manual_rpm < 1000 or manual_rpm > 6000:
                rumps.notification("Error", "Fan Control", "Please enter a valid RPM between 1000 and 6000.")
                return

            # Switch to manual mode if necessary
            if fan0.isFanInAuto(fan_ctl.getFanData()):
                fan0.changeFanMode(1)

            # Set the custom RPM
            fan0.setFanSpeed(manual_rpm)
            rumps.notification("Fan Speed", "Fan Control", f"Fan speed manually set to {manual_rpm} RPM.")

        except ValueError:
            rumps.notification("Invalid Input", "Fan Control", "Please enter a valid integer for RPM.")
        except Exception as e:
            rumps.notification("Error", "Fan Control", f"Failed to set manual fan speed: {e}")

    @rumps.clicked("Set Fan Curve/Default")
    @rumps.clicked("Set Fan Curve/Gaming")
    @rumps.clicked("Set Fan Curve/Silent")
    def on_select_curve(self, sender):
        self.selected_curve = sender.title
        rumps.notification("Fan Curve Selected", "Fan Control", f"{self.selected_curve} curve selected.")

    @rumps.clicked("Manual Fan Speed/2000 RPM")
    @rumps.clicked("Manual Fan Speed/3000 RPM")
    @rumps.clicked("Manual Fan Speed/4000 RPM")
    def on_set_manual_speed(self, sender):
        try:
            manual_rpm = int(sender.title.split(" ")[0])  # Extract the RPM value

            if fan0.isFanInAuto(fan_ctl.getFanData()):
                fan0.changeFanMode(1)

            fan0.setFanSpeed(manual_rpm)
            rumps.notification("Fan Speed", "Fan Control", f"Fan speed manually set to {manual_rpm} RPM.")

        except Exception as e:
            rumps.notification("Error", "Fan Control", f"Failed to set manual fan speed: {e}")

if __name__ == "__main__":
    app = FanControlApp()
    app.run()
