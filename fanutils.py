import subprocess
import os
import re, warnings, json
import time
import sys
from math import exp

#assert os.getuid() == 0, "Run with sudo to allow fan control access"

def sendCommand(command):
    process = os.popen("data/smc " + command)
    return process

executorFunction = sendCommand




class FanController:
    def __init__(self):
        pass

    def getAllControllerData(self):
        """
        Fetches all fan controller data using the 'smc list' command.
        """
        process = sendCommand("list")
        return process.read()

    def removeWhitespacesFromString(self, string):
        """
        Removes white spaces from the given string and converts it to a float.
        Returns -1 on failure.
        """
        try:
            integer = "".join([i for i in string if i != " "])
            return float(integer)
        except:
            return -1

    def getFanData(self):
        """
        Fetches fan data using the 'smc fans' command.
        """
        process = sendCommand("fans")
        return process.read()
    
    def getAverageCpuTemp(self, data):
        """
        Extracts and returns the average CPU temperature from the given data.
        """
        data = re.sub(r'\[|\]', '', data)
        pattern = re.compile(r'(Tp05|Tp0L|Tp0P|Tp0S|Tf04|Tf09|Tf0A|Tf0B|Tf0D|Tf0E|Tf44|Tf49|Tf4A|Tf4B|Tf4D|Tf4E)\s+(\d+\.\d+)')
        temps_match = pattern.findall(data)

        if not temps_match:
            warnings.warn("No matching CPU temperatures found.")
            return None

        all_temps_float = [float(temp) for _, temp in temps_match]
        average_temp = sum(all_temps_float) / len(all_temps_float)

        return average_temp


    def getHighestCpuTemp(self, data):
        """
        Extracts and returns the highest CPU temperature from the given data.
        """
        data = re.sub(r'\[|\]', '', data)
        pattern = re.compile(r'(Tp05|Tp0L|Tp0P|Tp0S|Tf04|Tf09|Tf0A|Tf0B|Tf0D|Tf0E|Tf44|Tf49|Tf4A|Tf4B|Tf4D|Tf4E)\s+(\d+\.\d+)')
        temps_match = pattern.findall(data)

        if not temps_match:
            warnings.warn("No matching CPU temperatures found.")
            return None

        all_temps_float = [float(temp) for _, temp in temps_match]
        highest_temp = max(all_temps_float, default=None)

        return highest_temp

    def getAverageGpuTemp(self, data):
        """
        Extracts and returns the average GPU temperature for M2 systems from the given data.
        """
        data = re.sub(r'\[|\]', '', data)
        # Updated pattern to match the M2 GPU temperature sensors
        pattern = re.compile(r'(Tg0f|Tg0j)\s+(\d+\.\d+)')
        temps_match = pattern.findall(data)

        if not temps_match:
            warnings.warn("No matching GPU temperatures found for M2.")
            return None

        all_temps_float = [float(temp) for _, temp in temps_match]
        average_temp = sum(all_temps_float) / len(all_temps_float)

        return average_temp

    def getTargetRpmPercent(self, activation_temp, max_temp, current_temp):
        """
        Calculates the target RPM percentage based on current, activation, and max temperatures.
        """
        return (current_temp - activation_temp) / (max_temp - activation_temp)


class Fan:
    def __init__(self, fan_id, controller=None, min_rpm=None, max_rpm=None):
        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.fan_id = fan_id
        self.controller = controller

        if (self.min_rpm is None) or (self.max_rpm is None):
            assert self.controller is not None, "Fan controller instance must be provided if min_rpm and max_rpm are not provided."
            self.autoSetBoundaries(self.controller.getFanData())
            warnings.warn("Auto set boundaries to: " + str(self.min_rpm) + " - " + str(self.max_rpm))
    
    def autoSetBoundaries(self, fan_data):
        """
        Sets the fan boundaries to the minimum and maximum speeds based on the given fan data.
        """
        min_speed, max_speed = self.getSpeedBoundaries(fan_data)
        self.min_rpm = min_speed
        self.max_rpm = max_speed

    def getSpeedBoundaries(self, fan_data):
        """
        Retrieves the minimum and maximum fan speeds from the given fan data.
        Returns a tuple (min_speed, max_speed).
        """
        try:
            # Extract minimal speed
            min_speed_match = re.search(r"Minimal speed:\s*(-?\d+\.\d+)", fan_data)
            min_speed = float(min_speed_match.group(1)) if min_speed_match else None

            # Extract maximum speed
            max_speed_match = re.search(r"Maximum speed:\s*(-?\d+\.\d+)", fan_data)
            max_speed = float(max_speed_match.group(1)) if max_speed_match else None

            # Return the values as a tuple
            return (min_speed, max_speed)
        
        except AttributeError:
            print("Could not find speed data in fan_data.")
            return (None, None)

    def setFanSpeed(self, rpm):
        """
        Sets the fan speed to the specified RPM.
        """
        executorFunction(" ".join(["fan", str(self.fan_id), "-v", str(rpm)]))

    def changeFanMode(self, mode):
        """
        Changes the fan mode to the specified mode (0 for auto, 1 for manual).
        """
        executorFunction(" ".join(["fan", str(self.fan_id), "-m", str(mode)]))

    def isFanInAuto(self, fan_data):
        """
        Returns True if the fan is in automatic mode based on the given fan data.
        """
        pattern = re.compile(r'(Mode:)\s+(\w+)')
        fan_data = pattern.findall(fan_data)
        return "automatic" in fan_data[self.fan_id]

    def isFanInForced(self, fan_data):
        """
        Returns True if the fan is in forced (manual) mode.
        """
        return not self.isFanInAuto(fan_data)

    def getTargetSpeed(self, fan_data):
        """
        Retrieves the current fan speed from the given fan data.
        """
        pattern = re.compile(r'Target speed: (-?\d+\.\d+)')
        fan_data = pattern.findall(fan_data)
        fan_speed = float(fan_data[self.fan_id])
        return 0 if fan_speed == -1 else fan_speed

    def getActualSpeed(self, fan_data):
        """
        Retrieves the actual fan speed from the given fan data.
        """
        pattern = re.compile(r'Actual speed: (-?\d+\.\d+)')
        fan_data = pattern.findall(fan_data)
        fan_speed = float(fan_data[self.fan_id])
        return 0 if fan_speed == -1 else fan_speed

    def isAtTarget(self, target_rpm, fan_data):
        """
        Checks if the fan is in forced mode and if the RPM matches the target RPM.
        """
        return self.isFanInForced(fan_data) and int(self.getFanSpeed(fan_data)) == int(target_rpm)

    def getTargetRpm(self, target_rpm_percent):
        """
        Calculates the target RPM based on the target percentage.
        """
        raw_target = ((self.max_rpm - self.min_rpm) * target_rpm_percent) + self.min_rpm
        if raw_target > self.max_rpm:
            return self.max_rpm
        elif raw_target > 0 and target_rpm_percent > 0:
            return raw_target
        else:
            return 0


class FanCurve:
    def __init__(self, profile_file):
        """
        Initializes the FanCurve with a profile loaded from a JSON file.
        
        Args:
            profile_file (str): Path to the profile JSON file.
        """
        self.load_profile(profile_file)

    def load_profile(self, profile_file):
        """
        Loads the fan curve profile from a JSON file.
        
        Args:
            profile_file (str): Path to the profile JSON file.
        """
        if not os.path.exists(profile_file):
            raise FileNotFoundError(f"Profile file {profile_file} not found")
        
        with open(profile_file, 'r') as f:
            self.profile = json.load(f)
        
        self.activation_temp = self.profile['activation_temp']
        self.max_temp = self.profile['max_temp']
        self.min_rpm = self.profile['min_rpm']
        self.max_rpm = self.profile['max_rpm']
        self.equation = self.profile['equation']
    
    def overrideMinMaxFromFan(self, fan: Fan):
        """
        Overrides the min and max RPM values with the min and max RPM values from the given fan.
        """
        self.min_rpm = fan.min_rpm
        self.max_rpm = fan.max_rpm

    def getFanRpm(self, current_temp):
        """
        Calculates the fan RPM based on the current temperature using the profile's equation.
        
        Args:
            current_temp (float): The current CPU temperature.
            
        Returns:
            float: The calculated fan RPM.
        """
        try:
            # Use eval() to dynamically evaluate the equation from the JSON file
            fan_rpm = eval(self.equation, {
                "current_temp": current_temp,
                "activation_temp": self.activation_temp,
                "max_temp": self.max_temp,
                "min_rpm": self.min_rpm,
                "max_rpm": self.max_rpm,
                "exp": exp  # Add math functions to the eval context
            })
            return fan_rpm
        except Exception as e:
            print(f"Error evaluating fan curve equation: {e}")
            return self.min_rpm


# Below was just testing purposes
if __name__ == "__main__":
    
    fan_ctl = FanController()
    fan0 = Fan(0, fan_ctl)
    data = fan_ctl.getAllControllerData()
    hiTemp = fan_ctl.getHighestCpuTemp(data)
    hiGpuTemp = fan_ctl.getAverageGpuTemp(data)

    print("Highest CPU Temp =", hiTemp)
    print("Average GPU Temp =", hiGpuTemp)
    print("Fan 0 actual =", fan0.getActualSpeed(fan_ctl.getFanData()))
    print("Fan 0 target =", fan0.getTargetSpeed(fan_ctl.getFanData()))
    print("Fan 0 boundaries =", fan0.getSpeedBoundaries(fan_ctl.getFanData()))
    print("Is in order:", fan0.isAtTarget(0, fan_ctl.getFanData()))

    if fan0.isFanInAuto(fan_ctl.getFanData()):
        print("Fan is in auto mode, setting manual speed.")
    else:
        print("Fan is in manual mode, setting auto and exiting.")
        fan0.changeFanMode(0)
