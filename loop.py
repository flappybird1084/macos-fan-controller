from fanutils import *
import time
import sys


timeinterval = 2
fancontroller = FanController()

# numfans = 2
fans = [Fan(2317, 6898, 0),
         Fan(2502, 7450, 1)] 
#define both fans such that you can have as many as you want without recoding
# technically the fanid argument is redundant here but i want the code to be usable in places other than this one



currenttemp = fancontroller.gethighestcputemp(fancontroller.getallcontrollerdata()) # do this once for all curve definitions
# if curves aren't defined with a generally correct current temp they may be at the wrong rpm for a second or two which bothers me
#fancurve(bottomanchor, topanchor, activationtemp, deactivationtemp, currentemp)
curve_old = [FanCurve((70, 100), (75, 70), (0,90), currenttemp),
          FanCurve((60, 95), (85, 80), (80,200), currenttemp),] 

curves = [FanCurve((70, 300), (75, 70), (0,80), currenttemp),
          FanCurve((78, 100), (80, 75), (80,90), currenttemp),
          FanCurve((73, 110), (82, 78), (78, 85), currenttemp),
          FanCurve((60, 95), (85, 70), (90,200), currenttemp),]  # define the curve for each fan, first argument is lowest temp, second is highest, third is lowest rpm, fourth is highest rpm, fifth is the current temp

# TODO: add a throttling fan curve - use PSTR key and powermetrics -s gpu_power + pmset bullshit to determine whether 
# gpu is pulling less watts @ high power mode on full utilization, then set fan speed to full blast immediately


# TODO: make special fan curve where from activation temp->deactivation temp the fan is set to a fixed speed, presumably min



onoffflag = False # on/off flag

# Parse command line arguments
for arg in sys.argv[1:]:
    if arg == '-on':
        onoffflag = True
    elif arg == '-off':
        onoffflag = False

# reset and exit if -off passed in
if onoffflag:
    print("\nCommencing custom fan controller. May God save your ears.\n")
else:
    print("\nWhat? You don't want to use my terrible piece of software?!\n")
    for fan in fans:
        fan.changefanmode(0)
    sys.exit()

# prep fans for custom operation -> set to auto and back to forced
for fan in fans:
    fan.changefanmode(0)
    fan.changefanmode(1)

while True:
    try:
        data = fancontroller.getallcontrollerdata()
        fandata = fancontroller.getfandata()
        cputemp = fancontroller.gethighestcputemp(data)
        print(f"Highest CPU temperature: {cputemp}°C")

        targetfanpercentagelist = []

        for i in curves:
            targetfanpercentagelist.append(i.getcurverpm_updateall(cputemp)) # calculate all curves & take highest rpm value for safety
        print(f"all percentages: {[i for i in targetfanpercentagelist]}")

        targetfanpercentage = max(targetfanpercentagelist)
        

        targetrpms = []
        for count, i in enumerate(fans):
            targetrpms.append(int(i.gettargetrpm(targetfanpercentage)))  # make int so controller can process properly

        for count, i in enumerate(targetrpms):
            fans[count].setfanspeed(i)
            print(f"fan {count} set to rpm {i}")

        
        time.sleep(timeinterval)

        for count, i in enumerate(fans):
            if not i.isfaninorder(targetrpms[count],fandata):
                i.changefanmode(0)
                i.changefanmode(1)
                print(f"fan {count} not in order, fixing...")
            else:
                print(f"fan {count} all in order!")

        print()
    


    except KeyboardInterrupt as e:
        print("\nExiting...")
        for fan in fans:
            fan.changefanmode(0)
            print(f"fan {fan.fanid} set to mode 0")


        sys.exit()

    except Exception as e:
        print("\nExiting...")
        for fan in fans:
            fan.changefanmode(0)
            print(f"fan {fan.fanid} set to mode 0")
            
        print(f"exception: {e}")
        sys.exit()


