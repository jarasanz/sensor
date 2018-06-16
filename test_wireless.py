#!/usr/bin/env python3

from wireless import Wireless
import json

wireless = Wireless("log")
wireless.getSystemWLANInfo()
print("*** Antes de getAssociationInfo")
print(json.dumps(wireless.wirelessinfo, indent=2))
wireless.getAssociationInfo()
print("*** Despues de getAssociationInfo")
print(json.dumps(wireless.wirelessinfo, indent=2))
#print("*** Longitud del array, que son los interfaces radio")
#print(len(wireless.wirelessinfo))
#print("*** Interface nombre lógico")
#print(wireless.wirelessinfo[0]["logical name"])


#
wlaninfo = {
    'ssid':'Temp',
    'status':'enable',
    'band':'auto',
    'bssid':'auto',
    'auth_method':'wpa-psk',
    'psk':'Helicon666',
    'eap':'',
    'phase2-auth':'',
    'username':'',
    'password':'',
    'ipconfig':'dhcp',
    'ipaddress':'',
    'netmask':'',
    'gateway':'',
    'dns1':'',
    'dns2':''
}
print(json.dumps(wireless.checkSSIDnmcli(wlaninfo), indent=2))

# print(wireless.addConnectionnmcli(wlaninfo))
# print(json.dumps(wireless.checkSSIDnmcli(wlaninfo), indent=2))
# print(wireless.connectWLAN(wlaninfo))

