#!/usr/bin/env python3

import logging

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
    
    def __init__(self, logname):
        """
            Initializate wireless
        """
        self.wirelessinfo = []
        self.getSystemWLANInfo()
        self.logger = logging.getLogger(logname+".Wireless")
        self.logger.info("Logging initialization of Wireless. Done.")
        
        
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
        import subprocess
        import sys
        
        wlaninfo = []
        
        # Let's get Hardware and Drivers information about wireless system
        # with the output of lshw
        command_shell = ["sudo", "/usr/bin/lshw", "-C", "network"]
        try:
            p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
        except OSError as error:
            errno, strerror = error.args
        
        if p1.returncode:
            # Pretty strange something was wrong with the call to lshw
            # so we can't get information... most probably is a Linux issue
            lshw_ok = False
        else:
            
            p2 = p1.stdout.decode("utf-8").strip().split("*-network")
            del p2[0]
            hw_w_interfaces = []
            for interface in p2:
                if "Wireless" in interface:
                    # This is a Wireless Interface
                    w_int = {}
                    for line in interface.strip().replace(": ",":").splitlines():
                        w_int[line.partition(":")[0].strip()] = line.partition(":")[2].strip()
                    hw_w_interfaces.append(w_int.copy())
        
        """
            hw_w_interfaces:
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
        wlaninfo = hw_w_interfaces.copy()
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
            try:
                p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as error:
                errno, strerror = error.args
        
            p2 = p1.stdout.decode("utf-8").strip()
            
            wlan_interface["Bands"] = p2.count("Band ")
            phy_info = p2
        
        # Let's get current regulatory domain
        for wlan_interface in wlaninfo:
            
            command_shell = ["sudo", "/sbin/iw", "reg", "get"]
            try:
                p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as error:
                errno, strerror = error.args
        
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
        import subprocess
                
        # Let's get current association status
        for wlan_interface in self.wirelessinfo:
            
            command_shell = ["sudo", "/sbin/iw", "dev", wlan_interface["logical name"], "link"]
            try:
                p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as error:
                errno, strerror = error.args
        
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
                        wlan_interface["connection"]["Virtual-AP"] = line.split()[2]
                    elif line.lstrip('\t').startswith("SSID"):
                        wlan_interface["connection"]["SSID"] = line.split()[1]
                    elif line.lstrip('\t').startswith("signal"):
                        wlan_interface["connection"]["signal"] = line.split()[1]
                    elif line.lstrip('\t').startswith("tx"):
                        wlan_interface["connection"]["tx_bitrate"] = line.split()[2]
                        wlan_interface["connection"]["MCS"] = line.split()[5]
                    elif line.lstrip('\t').startswith("dtim"):
                        wlan_interface["connection"]["dtim"] = line.split()[2]
                    elif line.lstrip('\t').startswith("beacon"):
                        wlan_interface["connection"]["beacon"] = line.split()[2]
                
                command_shell = ["sudo", "/sbin/iw", "dev", wlan_interface["logical name"], "info"]
                try:
                    p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError as error:
                    errno, strerror = error.args
        
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
                try:
                    p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError as error:
                    errno, strerror = error.args
        
                p2 = p1.stdout.decode("utf-8").strip()
                
                for line in p2.splitlines():
                    if line.strip().startswith("inet "):
                        wlan_interface["connection"]["ipaddress"] = line.split()[1].split("/")[0]
                        wlan_interface["connection"]["mask"] = line.split()[1].split("/")[1]
                    elif line.strip().startswith("inet6 "):
                        wlan_interface["connection"]["ipv6"] = line.split()[1].split("/")[0]
                        wlan_interface["connection"]["mask6"] = line.split()[1].split("/")[1]
                
                command_shell = ["ip", "route", "list"]
                try:
                    p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError as error:
                    errno, strerror = error.args
        
                p2 = p1.stdout.decode("utf-8").strip()
                
                for line in p2.splitlines():
                    if line.strip().startswith("default "):
                        wlan_interface["connection"]["gateway"] = line.split()[2]


        return self.wirelessinfo
        

    def connectWLAN (self, wlanobject):
        """
            Connects with indicated wlan network
        """
        
        print(wlanobject)
        
        return 

