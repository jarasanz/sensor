#!/usr/bin/env python3

import logging
from osshell import OSshell

class Wireless:

    """
        This module wraps the wireless interfaces in a system.
        Modify sudoers so the user of this script is part of sudoers AND
        NO PASSWORD IS REQUESTED:
        $ sudo visudo
        -> Add AT THE END OF THE FILE:
        <user>  ALL=(root) NOPASSWD: /sbin/iw, /usr/bin/nmcli, /usr/bin/lshw
        
        Example:
        bartolo     ALL=(root) NOPASSWD: /sbin/iw, /usr/bin/nmcli, /usr/bin/lshw
    """
    
    def __init__(self, logname="log"):
        """
            Initializate wireless
        """
        self.logname = logname + ".Wireless"
        self.logger = logging.getLogger(self.logname)
        self.logger.info("Logging initialization of Wireless. Done.")
        self.os = OSshell()
        self.wirelessinfo = self.getSystemWLANInfo()

        
    def getSystemWLANInfo(self):
        """
            Let's get all possible current information.
            Information is retrieved using:
            - Linux files
            - lshw
            - nmcli
            - iw
            Returns a list of dict/json object with RELEVANT information
            Each entry is a Wireless Interface, most probably will be just one
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        
        wlaninfo = []
        
        # Let's get Hardware and Drivers information about wireless system
        # with the output of lshw
        command_shell = ["sudo", "/usr/bin/lshw", "-C", "network"]
        status,p1,errors = self.os.runoscommand(command_shell)
        
        if p1.returncode:
            # Pretty strange something was wrong with the call to lshw
            # so we can't get information... most probably is a Linux issue
            lshw_ok = False
        else:
            
            p2 = p1.stdout.decode("utf-8").strip().split("*-network")
            del p2[0]
            hw_wlan_interfaces = []
            for interface in p2:
                if "Wireless" in interface:
                    # This is a Wireless Interface
                    wlan_int = {}
                    for line in interface.strip().replace(": ",":").splitlines():
                        wlan_int[line.partition(":")[0].strip()] = line.partition(":")[2].strip()
                    hw_wlan_interfaces.append(wlan_int.copy())
        
        """
            hw_wlan_interfaces:
            [
                {
                    "description": "Wireless interface",
                    "product": "Wireless 8260",
                    "vendor": "Intel Corporation",
                    "physical id": "0",
                    "bus info": "pci@0000:01:00.0",
                    "logical name": "wlp1s0",
                    "version": "3a",
                    "serial": "a0:c5:89:33:20:66",
                    "width": "64 bits",
                    "clock": "33MHz",
                    "capabilities": "pm msi pciexpress bus_master cap_list ethernet physical wireless",
                    "configuration": "broadcast=yes driver=iwlwifi driverversion=4.13.0-25-generic firmware=31.560484.0 ip=192.168.1.4 latency=0 link=yes multicast=yes wireless=IEEE 802.11",
                    "resources": "irq:283 memory:df100000-df101fff"
                }
            ]
        """
        wlaninfo = hw_wlan_interfaces.copy()
        for wlan_interface in wlaninfo:
            wlan_interface["phy"] = "phy" + wlan_interface["physical id"]
            try:
                del wlan_interface['bus info']
            except KeyError:
                # missing key
                print(sys.exc_info())
            try:
                del wlan_interface['version']
            except KeyError:
                # missing key
                print(sys.exc_info())
            try:
                del wlan_interface['capabilities']
            except KeyError:
                # missing key
                print(sys.exc_info())
            try:
                del wlan_interface['resources']
            except KeyError:
                # missing key
                print(sys.exc_info())
        
        
        
        # Let' get current information about the wireless phys
        for wlan_interface in wlaninfo:
            
            command_shell = ["sudo", "/sbin/iw", "phy", wlan_interface["phy"], "info"]
            
            status,p1,errors = self.os.runoscommand(command_shell)
            
            p2 = p1.stdout.decode("utf-8").strip()
            
            wlan_interface["Bands"] = p2.count("Band ")
            phy_info = p2
        
        # Let's get current regulatory domain
        for wlan_interface in wlaninfo:
            
            command_shell = ["sudo", "/sbin/iw", "reg", "get"]
            status,p1,errors = self.os.runoscommand(command_shell)
        
            p2 = p1.stdout.decode("utf-8").strip()
            
            control = False
            for line in p2.splitlines():
                
                if line.strip().startswith("phy#" + wlan_interface["physical id"]):
                    control = True
                
                if control:
                    if line.strip().startswith("country"):
                        wlan_interface["Country"] = line.strip().split("country ")[1].split(": ")[0]
                        wlan_interface["DFS"] = line.strip().split("country ")[1].split(": ")[1]
        
        
        self.wirelessinfo = wlaninfo.copy()
                
        return self.wirelessinfo
        
            
            
            
    def getAssociationInfo(self):
        """
            Return information about the association status
        """     
        # Attach to LOCAL SYSLOG
        logger = self.logger
                
        # Let's get current association status
        for wlan_interface in self.wirelessinfo:
            
            command_shell = ["sudo", "/sbin/iw", "dev", wlan_interface["logical name"], "link"]
            status,p1,errors = self.os.runoscommand(command_shell)
        
            p2 = p1.stdout.decode("utf-8").strip()
            
            if p2.startswith("Not"):
                # Not connected to WLAN
                wlan_interface["connected"] = False
            else:
                # Connected to WLAN
                wlan_interface["connected"] = True
                wlan_interface["connection"] = {}
                
                for line in p2.splitlines():
                    if line.lstrip('\t').startswith("Connected"):
                        wlan_interface["connection"]["bssid"] = line.split()[2]
                    elif line.lstrip('\t').startswith("SSID"):
                        wlan_interface["connection"]["SSID"] = line.split()[1]
                    elif line.lstrip('\t').startswith("signal"):
                        wlan_interface["connection"]["signal"] = line.split()[1]
                    elif line.lstrip('\t').startswith("tx"):
                        wlan_interface["connection"]["tx_bitrate"] = line.split()[2]
                        try:
                            wlan_interface["connection"]["MCS"] = line.split()[5]
                        except:
                            wlan_interface["connection"]["MCS"] = "undefined"
                    elif line.lstrip('\t').startswith("dtim"):
                        wlan_interface["connection"]["dtim"] = line.split()[2]
                    elif line.lstrip('\t').startswith("beacon"):
                        wlan_interface["connection"]["beacon"] = line.split()[2]
                
                command_shell = ["sudo", "/sbin/iw", "dev", wlan_interface["logical name"], "info"]
                status,p1,errors = self.os.runoscommand(command_shell)
        
                p2 = p1.stdout.decode("utf-8").strip()
                
                for line in p2.splitlines():
                    if line.strip().startswith("channel"):
                        wlan_interface["connection"]["channel"] = line.split()[1].strip()
                        wlan_interface["connection"]["width"] = line.split()[5].strip()
                        wlan_interface["connection"]["Freq"] = line.split()[2].strip("(")
                        wlan_interface["connection"]["CenterFreq"] = line.split()[8].strip()
                        if wlan_interface["connection"]["Freq"].startswith("2"):
                            wlan_interface["connection"]["Band"] = "2G"
                        elif wlan_interface["connection"]["Freq"].startswith("5"):
                            wlan_interface["connection"]["Band"] = "5G"
                    elif line.lstrip('\t').startswith("txpower"):
                        wlan_interface["connection"]["txpower"] = line.split()[1].strip()
            
        
                command_shell = ["ip", "a", "show", wlan_interface["logical name"]]
                status,p1,errors = self.os.runoscommand(command_shell)
        
                p2 = p1.stdout.decode("utf-8").strip()
                
                for line in p2.splitlines():
                    if line.strip().startswith("inet "):
                        wlan_interface["connection"]["ipaddress"] = line.split()[1].split("/")[0]
                        wlan_interface["connection"]["mask"] = line.split()[1].split("/")[1]
                    elif line.strip().startswith("inet6 "):
                        wlan_interface["connection"]["ipv6"] = line.split()[1].split("/")[0]
                        wlan_interface["connection"]["mask6"] = line.split()[1].split("/")[1]
                
                command_shell = ["ip", "route", "list"]
                status,p1,errors = self.os.runoscommand(command_shell)
        
                p2 = p1.stdout.decode("utf-8").strip()
                
                for line in p2.splitlines():
                    if line.strip().startswith("default "):
                        wlan_interface["connection"]["gateway"] = line.split()[2]

        return self.wirelessinfo
        


    def checkSSIDnmcli(self, wlaninfo):
        """
            Check if all values from <wlaninfo> are setup in nmcli configured connections
            -> ssid
            -> band
            -> bssid
            -> auth_method
            -> eap
            -> phase2-auth
            
            return [status, True/False, message, [error number], [error message] ]
            
            status: 
                 1  -> Found, all OK
                 2  -> SSID present, wrong BAND
                 3  -> SSID present, wrong BSSID
                 4  -> SSID present, auth_method wrong
                 5  -> SSID present, eap wrong
                 6  -> SSID present, phase2-auth wrong
                 7  -> OPEN auth_method, connect from scratch
                 8  -> SSID not found
                 20 -> error calling operating system
        """
        
        # Attach to LOCAL SYSLOG
        logger = self.logger
        
        logger.info("Searching " + wlaninfo["ssid"] + " in the list of nmcli connections...")
        command_shell = ["nmcli", "connection", "show", wlaninfo["ssid"]]
        status,p1,errors = self.os.runoscommand(command_shell)
        
        if status == 20:
            return [20, False, errors[0], errors[1], errors[2]]
        
        if p1.returncode:
            # ssid is not listed in the nmcli configured connections
            logger.info("SSID <" + wlaninfo["ssid"] + "> NOT found in the list of nmcli connections.")
            return [8, False, "SSID <" + wlaninfo["ssid"] + "> NOT found in the list of nmcli connections."]
        
        logger.info("SSID <" + wlaninfo["ssid"] + "> found in the list of nmcli connections.")
        # ssid is IN the list, let's check other parameters
        p2 = p1.stdout.decode("utf-8").strip()
        
        # if auth_method is "open", return with error, forcing to connect from scratch
        if wlaninfo["auth_method"] == "open":
            return [7, False, "Authentication method is OPEN, so connect from scratch."]
        
        # Let's adapt some formats and variables
        band = wlaninfo["band"]
        if wlaninfo["band"] == "auto": band = "--"
        bssid = wlaninfo["bssid"]
        if wlaninfo["bssid"] == "auto": bssid = "--"
        
        test = {
            "band":False,
            "bssid":False,
            "auth_method":False,
            "eap":False,
            "phase2-auth":False    
        }

        extract = {
            "band":"",
            "bssid":"",
            "auth_method":"",
            "eap":"",
            "phase2-auth":"",
            "phase2-autheap":""
        }
        
        for line in p2.splitlines():
            
            if line.startswith("802-11-wireless.band"):
                extract["band"] = line.split(":")[1].strip()
                continue
            if line.startswith("802-11-wireless.bssid"):
                extract["bssid"] = line.split(":")[1].strip()
                continue
            if line.startswith("802-11-wireless-security.key-mgmt"):
                extract["auth_method"] = line.split(":")[1].strip()
                continue
            if line.startswith("802-1x.eap"):
                extract["eap"] = line.split(":")[1].strip()
                continue
            if line.startswith("802-1x.eap"):
                extract["eap"] = line.split(":")[1].strip()
                continue
            if line.startswith("802-1x.phase2-autheap"):
                extract["phase2-autheap"] = line.split(":")[1].strip()
                continue
            if line.startswith("802-1x.phase2-auth"):
                extract["phase2-auth"] = line.split(":")[1].strip()
                continue
        
        # check band
        if extract["band"] == band:
            # band is OK
            logger.info("Configured RIGHT band <" + wlaninfo["band"] + "> in nmcli connection.")
            test["band"] = True
        else:
            # band NO OK
            logger.info("Configured band <" + wlaninfo["band"] + "> in nmcli connection is WRONG.")
            status = 2
            msg = "Band is wrong"
            
        # check bssid    
        if extract["bssid"] == bssid:
            # bssid is OK
            logger.info("Configured RIGHT bssid <" + wlaninfo["bssid"] + "> in nmcli connection.")
            test["bssid"] = True
        else:
            # bssid NO OK
            logger.info("Configured bssid <" + wlaninfo["bssid"] + "> in nmcli connection is WRONG.")
            status = 3
            msg = "bssid is wrong"
            
        # check auth_method, supported psk and 802.1x
        if extract["auth_method"] == wlaninfo["auth_method"]:
            # auth_method is OK
            logger.info("Configured RIGHT auth_method <" + wlaninfo["auth_method"] + "> in nmcli connection.")
            test["auth_method"] = True
            
            if wlaninfo["auth_method"] == "wpa-psk":
                # auth_method is PSK... nothing else to do
                test["eap"] = True
                test["phase2-auth"] = True
            
            else:
                # auth_method is 802.1x, have to check EAP and EAP-PHASE2-AUTHENTICATION
                if extract["eap"] == wlaninfo["eap"]:
                    logger.info("Configured RIGHT EAP <" + wlaninfo["eap"] + "> in nmcli connection.")
                    test["eap"] = True
                    
                    # Check EAP-PHASE2-AUTHENTICATION, peap and ttls supported
                    if wlaninfo["eap"] == "ttls":
                        # EAP is TTLS
                        # supported phase2 is mschapv2, it's stored in attribute 802-1x.phase2-autheap for ttls
                        if extract["phase2-autheap"] == wlaninfo["phase2-auth"]:
                            # phase2 is right
                            logger.info("Configured RIGHT EAP Phase2 Authentication <" + wlaninfo["phase2-auth"] + "> in nmcli connection.")
                            test["phase2-auth"] = True
                        else:
                            # phase2 is wrong
                            logger.info("Configured EAP Phase2 Authentication <" + wlaninfo["phase2-auth"] + "> in nmcli connection is WRONG.")
                            status = 6
                            msg = "EAP Phase2 Authentication is wrong"
                    else:
                        # EAP is PEAP
                        # supported phase2 is mschapv2, it's stored in attribute 802-1x.phase2-auth for peap
                        if extract["phase2-auth"] == wlaninfo["phase2-auth"]:
                            # phase2 is right
                            logger.info("Configured RIGHT EAP Phase2 Authentication <" + wlaninfo["phase2-auth"] + "> in nmcli connection.")
                            test["phase2-auth"] = True
                        else:
                            # phase2 is wrong
                            logger.info("Configured EAP Phase2 Authentication <" + wlaninfo["phase2-auth"] + "> in nmcli connection is WRONG.")
                            status = 6
                            msg = "EAP Phase2 Authentication is wrong"
                    
                else:
                    logger.info("Configured EAP <" + wlaninfo["eap"] + "> in nmcli connection is WRONG.")
                    status = 5
                    msg = "EAP is wrong (not TTLS/PEAP)"
        else:
            # auth_method is NO OK
            logger.info("Configured auth_method <" + wlaninfo["auth_method"] + "> in nmcli connection is WRONG.")
            status = 4
            msg = "Authentication method is wrong (not Open/PSK/802.1X)"
        
        # Let's define an OK Dict, in order to compare with the results
        test_ok = {
            "band":True,
            "bssid":True,
            "auth_method":True,
            "eap":True,
            "phase2-auth":True    
        }

        if test == test_ok:
            # PERFECT, connection in nmcli is ok.
            logger.info("The nmcli connection is OK, all connection options are set up according to the requierement !!!")
            return [1, True, "Connection in nmcli is ok."]
        else:
            # One or more parameters are wrong
            logger.info("The nmcli connection is NO OK, one or more connection options are NOT properly configured...")
            return [status, False, msg]


        
    def scanWLAN(self):
        return
    



    def addConnectionnmcli(self, wlaninfo):
        """
            Let's configure or modify a connection in nmcli

            wlaninfo = {
                "ssid":"Temp",
                "status":"enable",
                "band":"auto",
                "bssid":"auto",
                "auth_method":"wpa-psk",
                "eap":"",
                "psk":"password-psk",
                "ipconfig":"dhcp",
                "ipaddress":"",
                "netmask":"",
                "gateway":"",
                "dns1":"",
                "dns2":""
            }

            nmcli connection add 
                type wifi 
                con-name "Rivendel" 
                ifname wlp1s0 
                ssid "Rivendel" 
                802-11-wireless.band [a , bg]
                802-11-wireless.bssid 18:64:72:EA:F0:F2
                wifi-sec.key-mgmt wpa-eap 
                802-1x.eap peap 
                802-1x.identity "jorge" 
                802-1x.password "password" 
                802-1x.phase2-auth mschapv2 
                ipv4.method auto

            return [status, msg, errors]
                status:
                    1  -> OK, connection successfully added
                    2  -> NO OK, connection could not be added to nmcli
                    20 -> error calling operating system
            
        """
        import ipaddress
        
        # Attach to LOCAL SYSLOG
        logger = self.logger
        
        logger.info("Adding or modifying a connection in nmcli...")
        
        # Let's delete the connection, just in case
        command_shell = ["nmcli", "connection", "delete", wlaninfo["ssid"]]
        status,output,errors = self.os.runoscommand(command_shell)
        
        if status == 20:
            # OS error calling nmcli
            logger.info("Error deleting existing connection in nmcli...")

        
        # Let's add the connection with the options in wlaninfo
        command_shell = ["nmcli","connection","add"]
        command_shell += ["type","wifi"]
        command_shell += ["con-name",wlaninfo["ssid"]]
        
        # what interface to use, in case several interfaces
        if len(self.wirelessinfo) > 1:
            # Have several WLAN interfaces in the sensor
            logger.info("Several WLAN interfaces, choosing the right one...")
            if wlaninfo["band"] == "a":
                # 5GHz band, have to select a 5GHz capable interface
                logger.info("Interface must support 5GHz band... searching...")
                interface_ok = False
                for wlaninterface in self.wirelessinfo:
                    if wlaninterface["Bands"] == 2:
                        # This interface is 5GHz capable
                        logger.info("Found interface capable of 5GHz: <" + str(wlaninterface["logical name"]) + ">.")
                        command_shell += ["ifname",wlaninterface["logical name"]]
                        interface_ok = True
                        break
                if not interface_ok:
                    # It's not possible to run the TEST in 5GHz...
                    # none of the available interfaces can support 5GHz
                    # Let's use the first one available
                    logger.info("None of the available WLAN interfaces support 5GHz, connection will default to <auto>")
                    logger.info("Interface to use <" + str(self.wirelessinfo[0]["logical name"]) + ">.")
                    command_shell += ["ifname",self.wirelessinfo[0]["logical name"]]
                        
            else: # wlaninfo["band"] == "auto" or "bg"
                # Choose any (the first for instance) as Band doesn't matter
                logger.info("Band is auto or bg, interface capabilities are not important, choosing the first available WLAN interface.")
                logger.info("Interface to use <" + str(self.wirelessinfo[0]["logical name"]) + ">.")
                command_shell += ["ifname",self.wirelessinfo[0]["logical name"]]
                
        else:
            # Just one WLAN interface
            logger.info("Only one interface in the SENSOR, using it.")
            logger.info("Interface to use <" + str(self.wirelessinfo[0]["logical name"]) + ">.")
            command_shell += ["ifname",self.wirelessinfo[0]["logical name"]]
        
        # SSID
        command_shell += ["ssid",wlaninfo["ssid"]]
        
        # BAND
        if wlaninfo["band"] == "auto":
            logger.info("Setting BAND to auto...")
            # No need to add a band, let the OS and AP negotiate
        else: # Assign the band
            logger.info("Setting BAND to <" + str(wlaninfo["band"]) + ">...")
            command_shell += ["802-11-wireless.band", wlaninfo["band"]]

        # BSSID or Virtul-AP or VAP
        if wlaninfo["bssid"] == "auto":
            logger.info("Setting BSSID to auto...")
            # No need to add a BSSID, OS and AP will negotiate
        else: # Assign the bssid
            logger.info("Setting BSSID to <" + str(wlaninfo["bssid"]) + ">...")
            command_shell += ["802-11-wireless.bssid", wlaninfo["bssid"]]
        
        # Authentication
        if wlaninfo["auth_method"] == "open":
            logger.info("Setting authentication to OPEN...")
            # No need to add anything else
        elif wlaninfo["auth_method"] == "wpa-psk":
            # Pre-Shared Key with AES
            logger.info("Setting authentication to PreShared Key and AES (WPA2-PSK)...")
            command_shell += ["802-11-wireless-security.key-mgmt", wlaninfo["auth_method"]]
            command_shell += ["802-11-wireless-security.psk", wlaninfo["psk"]]
        else:
            # 802.1X Authentication - wpa-eap
            logger.info("Setting authentication to 802.1X...")
            command_shell += ["802-11-wireless-security.key-mgmt", wlaninfo["auth_method"]]
            if wlaninfo["eap"] == "peap":
                # EAP is PEAP
                logger.info("Setting EAP method to <" + str(wlaninfo["eap"]) + ">...")
                command_shell += ["802-1x.eap", wlaninfo["eap"]]
                logger.info("Setting USERNAME and PASSWORD for PEAP...")
                command_shell += ["802-1x.identity", wlaninfo["username"]]
                command_shell += ["802-1x.password", wlaninfo["password"]]
                logger.info("Setting Phase2 to <" + str(wlaninfo["phase2-auth"]) + ">...")
                command_shell += ["802-1x.phase2-auth", wlaninfo["phase2-auth"]]
            else:
                # EAP is TTLS
                logger.info("Setting EAP method to <" + str(wlaninfo["eap"]) + ">...")
                command_shell += ["802-1x.eap", wlaninfo["eap"]]
                logger.info("Setting USERNAME and PASSWORD for PEAP...")
                command_shell += ["802-1x.identity", wlaninfo["username"]]
                command_shell += ["802-1x.password", wlaninfo["password"]]
                logger.info("Setting Phase2 to <" + str(wlaninfo["phase2-auth"]) + ">...")
                command_shell += ["802-1x.phase2-autheap", wlaninfo["phase2-auth"]]
            
        # IPv4 Configuration
        if wlaninfo["ipconfig"] == "dhcp":
            # auto configuration
            logger.info("Setting IPv4 configuration to <" + str(wlaninfo["ipconfig"]) + ">...")
            command_shell += ["ipv4.method", "auto"]
        else:
            # manual configuration
            logger.info("Setting IPv4 configuration to <" + str(wlaninfo["ipconfig"]) + ">...")
            command_shell += ["ipv4.method", "manual"]
            # IPv4 address
            ip_interface = ipaddress.IPv4Interface(wlaninfo["ipaddress"] + "/" + wlaninfo["netmask"])
            logger.info("Setting IPv4 address to <" + str(ip_interface) + ">...")
            command_shell += ["ipv4.addresses", str(ip_interface)]
            # IPv4 gateway
            gateway = ipaddress.IPv4Address(wlaninfo["gateway"])
            logger.info("Setting IPv4 Gateway to <" + str(wlaninfo["gateway"]) + ">...")
            if not gateway in ip_interface.network:
                logger.warning("Gateway IPv4 address is not in the network range... Setting gateway in any case.")
            command_shell += ["ipv4.gateway", str(gateway)]
            # IPv4 DNS
            if wlaninfo["dns2"] == "":
                # Only one DNS server
                dns = wlaninfo["dns1"]
            else:
                # Two DNS servers
                dns = wlaninfo["dns1"] + "," + wlaninfo["dns2"]
            logger.info("Setting IPv4 DNS to <" + str(dns) + ">...")
            command_shell += ["ipv4.dns", dns]
        
        # Command to call nmcli is complete
        logger.info("nmcli command before calling runOSCommand <" + str(command_shell) + ">.")
        logger.info("Calling Operating System to add connection to nmcli connections list...")
        status,output,errors = self.os.runoscommand(command_shell)
        
        if status > 1:
            # Something went wrong calling the Operating System
            logger.warning("ERROR calling nmcli to add <" + str(wlaninfo["ssid"]) + "> to the list of nmcli connections...")
            logger.warning(str(output))
            logger.warning(str(errors[0]))
            logger.warning(str(errors[1]))
            logger.warning(str(errors[2]))
            return [20, output, errors]
        else:
            # Call to OS was right, let's see the result of calling nmcli
            if output.returncode == 0:
                # New connection successfully added to the list of nmcli connections
                logger.info("SUCCESS - connection <" + str(wlaninfo["ssid"]) + "> added to the list of nmcli connections.")
                return [1, output, errors]
            else:
                # Some problem with the call to nmcli
                logger.info("<" + str(wlaninfo["ssid"]) + "> added to the list of nmcli connections.")
                logger.info(str(output))
                return [2, output, errors]



    def checkSSIDair(self, wlaninfo, force_scan=False):
        """
            Check if the ssid in wlaninfo is present in the "air"
            Will use default information from kernel, from last scans
            If force_scan=True, try to rescan
            
            nmcli device wifi rescan
            nmcli -f signal,ssid,bssid,chan,in-use device wifi
            
        """
        import subprocess
        import sys
        
        # Attach to LOCAL SYSLOG
        logger = self.logger
        
        # Depending on force_scan will force rescan
        if force_scan:
            # Force to scan
            command_shell = ["nmcli","device","wifi","rescan"]
            status,output,errors = self.os.runoscommand(command_shell)
#            if status > 1:
#                # Problem with the Operating System
#                # using information stored in the kernel from last scans
#            else:
#                # Call OK to Operating System
#                if output.returncode == 1:
#                    # Too frequent scans

        # Calling scan results
        command_shell = ["nmcli","-f","ssid,bssid,signal,chan,in-use","device","wifi"]
        status,output,errors = self.os.runoscommand(command_shell)
        if status > 1:
            #Problem calling the Operating System
            return [2,"Problem scanning, could NOT receive information from active SSIDs..."]
        else:
            p2 = output.stdout.decode("utf-8").strip()
            if wlaninfo["ssid"] in p2:
                return [1, "SSID <"+wlaninfo["ssid"]+"> is in the list of visible SSIDs."]

        
    def checkcurrentwlan(self, wlaninfo):
        """
        Check if the current, active connection to WLAN is equal to the requested by wlaninfo
        :param wlaninfo: WLAN parameters to check
        :return: [status, message]
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        # Instantiate an OSshell object for calling the Operating System
        os = OSshell(self.logname)
        # Let's get current wlan
        command_shell = ["nmcli", "connection", "show", "--active", wlaninfo["ssid"]]
        status,output,errors = os.runoscommand(command_shell)
        if status > 1:
            #Problem calling the Operating System
            return [2, "Problem scanning, could NOT receive information from active SSIDs..."]
        else:
            p1 = output.stdout.decode("utf-8").strip()
            # Check if current ssid match with wlaninfo
            if wlaninfo["ssid"] in p1:
                # The ACTIVE ssid IS the one in wlaninfo
                # get detailed information about the current wlan
                associatedwlan = self.getAssociationInfo()
                """
                Esto tiene mucha miga...
                """
            else:
                # The ACTIVE ssid is NOT the one in wlaninfo
                logger.info("Current SSID is not equal to needed SSID <" + str(wlaninfo["ssid"]) + ">. Will have to disconnect and connect to the right one.")
                return [3, "Current SSID is not equal to needed SSID <" + str(wlaninfo["ssid"]) + ">. Will have to disconnect and connect to the right one."]



    def connectWLAN(self, wlaninfo):
        """
            Connects with indicated wlan network, using wlaninfo:
            
            wlaninfo = {
                "ssid":"Temp",
                "status":"enable",
                "band":"auto",
                "vap":"auto",
                "auth_method":"wpa-psk",
                "eap":"",
                "psk":"password-psk",
                "ipconfig":"dhcp",
                "ipaddress":"",
                "netmask":"",
                "gateway":"",
                "dns1":"",
                "dns2":""
            }
        """
        import subprocess
        import sys
        
        # Attach to LOCAL SYSLOG
        logger = self.logger
        
        # Check if wlaninfo is ENABLED... otherwise return
        if wlaninfo["status"] == "disable":
            # WLAN network disabled, no connection to make
            logger.info("WLAN <" + str(wlaninfo["ssid"]) + ">, administrative disable. No connection will be made.")
            return [6, "WLAN <" + str(wlaninfo["ssid"]) + ">, administrative disable. No connection will be made."]
        
        # Let's check if all configured paramenters for the ssid 
        # are already in the list of nmcli connections
        logger.info("Check if " + wlaninfo["ssid"] + " is in the nmcli already configured connections...")
        if self.checkSSIDnmcli(wlaninfo)[0] > 1:
            # Not in the list or some parameter is wrong
            logger.info("Let's configure the connection in nmcli...")
            if self.addConnectionnmcli(wlaninfo)[0] > 1:
                # Could NOT add the connection to nmcli... have to return with no results
                return [2, "Could NOT create a connection in nmcli."]
        
        # WLAN network in wlaninfo is already available in the list of nmcli connections
        # logger.info("WLAN network <" + str(wlaninfo["ssid"]) + "> available in the list of nmcli connections...")
        
        # Check that the WLAN network is present in the air
        logger.info("Checking that <" + str(wlaninfo["ssid"]) + "> is seen in the air...")
        if self.checkSSIDair(wlaninfo, True)[0] > 1:
            # SSID not found in the list of visible SSIDs
            logger.warning("SSID <" + str(wlaninfo["ssid"]) + ">, NOT RF visible... CAN'T CONNECT")
            return [3, "SSID <"+wlaninfo["ssid"]+">, NOT visible in the last scanned... CAN'T CONNECT"]
        logger.info("SSID <" + str(wlaninfo["ssid"]) + "> is RF visible... can connect.")

        #Check if the current connection is right
        logger.info("Checking if current connection is ok, so can be used without modification...")


        # Connect
        logger.info("Connecting with the SSID <" + str(wlaninfo["ssid"]) + ">...")
        command_shell = ["nmcli","connection","up",wlaninfo["ssid"]]
        status,output,errors = self.os.runoscommand(command_shell)
        
        if status > 1:
            # ERROR calling Operating System
            logger.info("ERROR calling the Operating System for connecting to the right SSID.")
            return [4, "ERROR in the Operating System call when changing to the SSID."]
        else:
            if output.returncode == 0:
                # SUCCESS!!! Connected to SSID
                logger.info("SUCCESS!!! Successfully connected to SSID <" + str(wlaninfo["ssid"]) + ">.")
                return [1, output.stdout.decode("utf-8").strip()]
            else:
                # Problem in nmcli
                logger.info("Problem in nmcli connecting to SSID <" + str(wlaninfo["ssid"]) + ">.")
                return [5, output.stdout.decode("utf-8").strip()]
                
    def pprint(self):
        import json
        return print(json.dumps(self.wirelessinfo, indent=2))





