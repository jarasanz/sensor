#!/usr/bin/env python3

import json
from sensor_v10 import Sensor

s1 = Sensor()

#print(json.dumps(s1.sensor["sensorinfo"], indent=4))
#print("\n****************************************\n")
#print(json.dumps(s1.sensor["wlans"], indent=4))
#print("\n****************************************\n")
#print(json.dumps(s1.showTest("Temp"), indent=4))
print("\n****************************************\n")
print(json.dumps(s1.connectWLAN(wlanid=1), indent=2))
