#!/usr/bin/env python3

from wireless import Wireless
import json

wireless = Wireless("log")
#wireless.getSystemWLANInfo()
print("*** Antes de getAssociationInfo")
print(json.dumps(wireless.wirelessinfo, indent=2))
wireless.getAssociationInfo()
print("*** Despues de getAssociationInfo")
print(json.dumps(wireless.wirelessinfo, indent=2))

