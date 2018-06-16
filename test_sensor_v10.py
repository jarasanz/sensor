#!/usr/bin/env python3

import json
from sensor_v10 import Sensor

s1 = Sensor()

# print(json.dumps(s1.sensor, indent=2))
# print("\n****************************************\n")
# print(json.dumps(s1.sensor["sensorinfo"], indent=2))
# print("\n****************************************\n")
#print(json.dumps(s1.sensor["wlans"], indent=4))
# print("\n****************************************\n")
# print(json.dumps(s1.showTest(), indent=4))
# print("\n****************************************\n")
# print(json.dumps(s1.connectWLAN(wlanid=2), indent=2))
# print("\n****************************************\n")
# print(json.dumps(s1.wlan.wirelessinfo, indent=2))
# print("\n****************************************\n")
# print(json.dumps(s1.runalltests(), indent=2))
# print("\n****************************************\n")
# print(json.dumps(s1.gettestinfo(wlanid=1,testname="delay")[1], indent=2))
# print("\n****************************************\n")
# test = s1.gettestinfo(wlanid=1,testname="delay")[1]
# print(json.dumps(s1.runsingletest(1, test), indent=2))
# error, test = s1.gettestinfo(wlanid=1,testname="delay")
# error, result = s1.runsingletest(1, test)
# # i = s1.getindexwlans(1)
# print(json.dumps(s1.sensor["wlans"], indent=2))