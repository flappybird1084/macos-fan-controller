import subprocess, os
from getpw import getsudopassword
#from cputemp import getsudopassword
import re
import time

class FanController:
    def __init__(self):
        pass
    

    def getallcontrollerdata(self):
        process = os.popen("./smc list")
        return process.read()
    
    def removewhitespacesfromstring(self, string):
        try:
            integer = ""
            for i in string:
                if not i == " ":
                    integer = integer + i
            return float(integer)
        except:
            return -1
    
    def getfandata(self):
        process = os.popen("./smc fans")
        return process.read()

    def gethighestcputemp(self, data):

        data = re.sub(r'\[|\]', '', data)        

        # Define regex pattern to match desired CPU temperatures (similar to your egrep command)
        pattern = re.compile(r'(Te05|Te0L|Te0P|Te0S|Tf04|Tf09|Tf0A|Tf0B|Tf0D|Tf0E|Tf44|Tf49|Tf4A|Tf4B|Tf4D|Tf4E)\s+(\d+\.\d+)')

        temps_match = pattern.findall(data)

        if not temps_match:
            print("No matching CPU temperatures found.")
            return None

        alltempsfloat = [float(temp) for _, temp in temps_match]

        highesttemp = max(alltempsfloat, default=None)

        #print(f"Highest CPU temperature: {highesttemp}°C")
        return highesttemp
    
    def gettargetrpmpercent(self, activationtemp, maxtemp, currenttemp):
        return((currenttemp-activationtemp)/(maxtemp-activationtemp))
        #example: a = 30, m = 50, c = 40
        # will return 0.5 or 50% fan speed
    

class Fan:
    def __init__(self, minrpm, maxrpm, fanid):
        self.minrpm = minrpm
        self.maxrpm = maxrpm
        self.fanid = fanid
        self.fancontroller = FanController()

    def setfanspeed(self, rpm):
        fan = self.fanid
        #./smc fan 1 -v 4000
        #need to put in stdin to subprocess

        rpmchanger = subprocess.Popen(["sudo","./smc", "fan", str(fan),"-v", str(rpm)], stdin= subprocess.PIPE)
        getsudopassword(rpmchanger)
        
        #print("fan "+str(fan)+" successfully set to rpm "+str(rpm))

    def changefanmode(self, mode):
        fan = self.fanid
        # Mode 0 is automatic, 1 is manual
        modechanger = subprocess.Popen(["sudo", "./smc", "fan", str(fan), "-m", str(mode)])
        getsudopassword(modechanger)

    def isfaninauto(self, fandata):
        pattern = re.compile(r'(Mode:)\s+(\w+)')
        fandata = pattern.findall(fandata)
        #print(data)
        return ("automatic" in fandata[self.fanid])
    
    def isfaninforced(self, fandata):
        return not self.isfaninauto(fandata)
    
    def getfanspeed(self, fandata):
        pattern = re.compile(r'Target speed: (-?\d+\.\d+)')
        fandata = pattern.findall(fandata)
        #print(data)
        fanspeed = float(fandata[self.fanid])
        if fanspeed == -1:
            return 0
        else:
            return fanspeed
        
    def isfaninorder(self,targetrpm, fandata): # is fan forced and rpm match
        return (self.isfaninforced(fandata) and int(self.getfanspeed(fandata))==int(targetrpm))
    

    def gettargetrpm(self, targetrpmpercent):
        minrpm = self.minrpm
        maxrpm = self.maxrpm

        rawtarget = ((maxrpm-minrpm)*targetrpmpercent)+minrpm
        
        if rawtarget>maxrpm:
            return maxrpm
        elif rawtarget>0 and targetrpmpercent>0:
            return rawtarget
        else:
            return 0
        
class FanCurve():
    def __init__(self, anchors, activations, jurisdiction, currenttemp, isActivated=False):
        self.mintempanchor = anchors[0]
        self.maxtempanchor = anchors[1]
        self.activationtemp = activations[0]
        self.deactivationtemp = activations[1]
        self.bottomjurisdiction = jurisdiction[0]
        self.topjurisdiction = jurisdiction[1]
        self.currenttemp = currenttemp
        self.isActivated = isActivated

    def updatecurrenttemp(self, currenttemp):
        self.currenttemp = currenttemp

    def updateactivationstate(self, currenttemp):
        if currenttemp>=self.activationtemp and not self.isActivated:
            self.isActivated = True

        elif self.isActivated and not currenttemp>=self.deactivationtemp:
            self.isActivated = False

    def getactivated(self):
        return self.isActivated

    def standardcurve(self, activationtemp, maxtemp, currenttemp):
        return((currenttemp-activationtemp)/(maxtemp-activationtemp))
        #example: a = 30, m = 50, c = 40
        # will return 0.5 or 50% fan speed
    
    def getcurverpm(self):
        if self.isActivated:
            if self.currenttemp>=self.bottomjurisdiction and self.currenttemp<=self.topjurisdiction:
                return self.standardcurve(self.mintempanchor, self.maxtempanchor, self.currenttemp)
        else:
            return 0
        
    def getcurverpm_updateall(self, currenttemp):
        self.updatecurrenttemp(currenttemp)
        self.updateactivationstate(currenttemp)
        return self.getcurverpm()



    
'''
    

    
# Instantiate FanController object with the same parameters as before
fancontroller = FanController()

# Get and split data from the Fan Controller
data = fancontroller.getallcontrollerdata()

# Print data and highest CPU/Processor temperature
#print(data)

#print(fancontroller.gethighestcputemp(data))

fandata = fancontroller.getfandata()
print(f"fandata: {fandata}")

fan0 = Fan(2317, 6898, 0)
#print(fan0.isfaninauto(fandata))
print(fan0.getfanspeed(fandata))

print(fan0.isfaninorder(0, fandata))

# fancurve = FanCurve(60,90,70,62,fancontroller.gethighestcputemp(data), True)

# curve is 60->90 activates at 70 celsius and deactivates at 62 celsius. controller set to cpu temp and curve starts in activation state

# while True:
#     data  = fancontroller.getallcontrollerdata()
#     print(fancurve.getcurverpm_updateall(fancontroller.gethighestcputemp(data)))
#     print(fancurve.isActivated)
#     time.sleep(1)


'''