#!/usr/bin/env python3


# Modules used along all functions for local syslog
import logging
from logging.handlers import SysLogHandler

# Used along the functions for local syslog
logname = "WLANsensor"

# Configuration file
configuration_file = "/home/ale/sensor/wlansensor.json"

# Connectivity Failures File
failures_file = "/home/ale/sensor/sensorwatchdog.json"


def ReadConfigFile (config_file=configuration_file):
    """ Reads the config file if exists and returns sensor_info
        with all the current information about the sensor
        If the file does not exist, returns an empty sensor_info
    """
    
    import os.path
    import json
    
    # Attach to LOCAL SYSLOG
    logger = logging.getLogger(logname)
    
    try:
        with open(config_file) as json_data:
            sensor_info = json.load(json_data)
            logger.info(config_file + " successfully read.")
            logger.info("wlansensor information restored in sensor_info")
    except OSError as error:
        errno, strerror = error.args
        if errno == 2:
            # File does not exists
            logger.info("Could not find " + config_file
                + " ... setting sensor_info to {}")
            sensor_info = {}

    return sensor_info



def WriteConfigFile (sensor_info, config_file=configuration_file):
    """ Writes to file the updated information of sensor_info
    """
    
    import os.path
    import json
    
    # Attach to Local SYSLOG
    localsyslog = logging.getLogger(logname)
    localsyslog.info("Writing sensor_info to file <" + config_file + ">.")
    
    try:
        with open(config_file, 'w') as json_data:
            json.dump(config_file, json_data, indent=4)
            localsyslog.info("sensor_info successfully written to file <"
                + config_file + ">.")

    except OSError as error:
        errno, strerror = error.args
        if errno == 2:
            # File does not exists
            localsyslog.info("WriteConfigFile ERROR: " + strerror)

    return sensor_info
    
    

def CheckIPConnection (ipaddress):
    """ Check the LAN association
        returns True if connectivity with 'ipaddress' is ok
        returns False if connectivity with 'ipaddress' is impossible
    """
    import subprocess

    # /bin/ping will retun 0 if there is ICMP echo response
    # will return 1 if there is NO ICMP echo response

    p = subprocess.run(["/bin/ping","-c2 -w1",ipaddress], stdout=subprocess.PIPE)

    # in Python 0 is False, but it's OK for ping
    # in Python 1 is True, but it's NOK for ping
    # so let's change the rule...
    return not p.returncode



def ReadConnectivityFailuresFile (failures_file=failures_file):
    """ Reads the Connectivity Failures file
        Returns the followed connection failures dict/json object:
        {
            "connectivity_failures":0
        }    

        {
            "connectivity_failures":2,
            "connectivity_failures_list":[
                {
                    "connfail_time":"2018-01-13 11:13:09",
                    "connfail_code":401,
                    "connfail_info":"Not connected to WLAN.",
                    "connfail_order":1
                },
                {
                    "connfail_time":"2018-01-13 11:13:45",
                    "connfail_code":402,
                    "connfail_info":"There is no CONNECTION defined in nmcli.",
                    "connfail_order":2
                }
            ]
        }
    """
    
    import os.path
    import json
    
    # Attach to Local SYSLOG
    localsyslog = logging.getLogger(logname)
    
    # Read the Connectivity Failures File
    localsyslog.info("Reading Connectivity Failures File...")
    failures = {}
    try:
        with open(failures_file) as json_data:
            failures = json.load(json_data)

    except OSError as error:
        errno, strerror = error.args
        if errno == 2:
            # File does not exists
            localsyslog.info("Could not find " + failures_file 
                + ". Considering 0 errors.")
            failures["connectivity_failures"] = 0

    localsyslog.info(failures_file + " successfully read.")
    localsyslog.info("Connectivity Failures: <" 
        + str(failures["connectivity_failures"]) + ">")
    
    return failures
    


def WriteConnectivityFailuresFile (failures, failures_file=failures_file):
    """ Writes the dict/json object to Connectivity Failures file
        Returns 
        --> True: Everything OK
        --> False: Something went wrong...
        {
            "connectivity_failures":0
        }    

        {
            "connectivity_failures":2,
            "connectivity_failures_list":[
                {
                    "connfail_time":"2018-01-13 11:13:09",
                    "connfail_code":401,
                    "connfail_info":"Not connected to WLAN.",
                    "connfail_order":1
                },
                {
                    "connfail_time":"2018-01-13 11:13:45",
                    "connfail_code":402,
                    "connfail_info":"There is no CONNECTION defined in nmcli.",
                    "connfail_order":2
                }
            ]
        }
    """
    
    import os.path
    import json
    
    # Attach to Local SYSLOG
    localsyslog = logging.getLogger(logname)
    
    # Read the Connectivity Failures File
    localsyslog.info("WriteConnectivityFailuresFile: Writing Connectivity "
        + "Failures to File...")
    
    try:
        with open(failures_file, 'w') as json_data:
            json.dump(failures, json_data, indent=4)

    except OSError as error:
        errno, strerror = error.args
        if errno == 2:
            # File does not exists
            localsyslog.info("WriteConnectivityFailuresFile: Could not find " 
                + failures_file + ". Creating file...")
            return False
    
    localsyslog.info("WriteConnectivityFailuresFile: " 
        + str(failures) + " successfully written to " + failures_file)
    return True

    
    
def ConnectWLAN (sensor_info, wlaninfo):
    """
        Try to connect to SSID in sensor_info, using information from wlaninfo
        Will use nmcli and iw system tools
        Will assume that sensor has already been connected to that SSID, 
        and nmcli has a connection available.
        Return True - If connection is established
        Return False / Exits program - If connection is impossible
        Writes to ~/connectionfailures.json so watchdog can take actions...
    """
    import subprocess
    import sys
    import time
    
    # Attach to Local SYSLOG
    localsyslog = logging.getLogger(logname)
    
    localsyslog.info("ConnectWLAN: SENSOR not connected to WLAN, let's try to "
        + "connect to right SSID: " + sensor_info["wlansensor_info"]["ssid"])
    
    # Reading failures file
    localsyslog.info("ConnectWLAN: Reading failures from "
        + "sensorwatchdog file...")
    failures = ReadConnectivityFailuresFile()
    localsyslog.info("ConnectWLAN: Failures up to now: " 
        + failures["connectivity_failures"])
    
    #
    localsyslog.info("ConnectWLAN: Will check if a valid connection is "
        + "available in nmcli...")
    
    # Check if a valid connection has already been configured
    command_shell = ["/usr/bin/nmcli", "connection", "show"]
    p1 = subprocess.run(command_shell, stdout=subprocess.PIPE)
    p2 = p1.stdout.decode("utf-8").splitlines()
    
    connections = []
    keys = []
    for i,line in enumerate(p2):
        connection = {}
        if i == 0 :
            # First line with headers
            # NAME               UUID                                  TYPE             DEVICE
            for j in line.split():
                keys.append(j)
        
        else:
            for j in range(4):
                connection[keys[j]] = line.split()[j]
            connections.append(connection.copy())
    
    localsyslog.info("ConnectWLAN: Founded <" + len(connections) 
        + "> connections in nmcli.")
        
    # Let's check if one of this connections is linked with the right SSID
    for connection in connections:
        if connection[keys[0]] == sensor_info["wlansensor_info"]["ssid"]:
            # There is a valid connection
            valid_connection = True
            
    if not valid_connection:
            # Couldn't find a configured connection in nmcli 
            # There is NO connection that matches the needed SSID !!!
            # It's time to QUIT
            # But let's write first the failures into file
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            
            localsyslog.critical("ConnectWLAN: Oh, oh... "
                + "Not connected to WLAN... "
                + "And COULDN'T find a valid connection in nmcli, "
                + "in order to connect to the right SSID"
                + "Have to quit.")
            localsyslog.debug("ConnectWLAN: The WLANsensor is NOT connected "
                + "to WLAN.")
            localsyslog.debug("ConnectWLAN: NO valid connections were found"
                + " in nmcli.")

            localsyslog.info("ConnectWLAN: NO valid connections were found "
                + "in nmcli.")
            localsyslog.info("ConnectWLAN: Please check WLAN connectivity.")
            localsyslog.debug("ConnectWLAN: Obviously have to quit...")
            
            # Update failures object and write to file
            failures["connectivity_failures"] += 1
            failure = {}
            failure["connfail_time"] = timestamp
            failure["connfail_code"] = 402
            failure["connfail_info"] = "COULDN'T find a valid connection in nmcli in order to connect to the right SSID."
            failure["connfail_order"] = len(failures["connectivity_failures_list"]) + 1
            failures["connectivity_failures_list"].append(failure)
            localsyslog.info("ConnectWLAN: Writing failures to sensorwatchdog "
                + "file...")
            WriteConnectivityFailuresFile(failures)
            
            exit_msg = "WLANsensor NOT connected to WLAN, tried to find a "
            exit_msg += "valid stored connection in nmcli, "
            exit_msg += "but there is NO one with the right SSID (" 
            exit_msg += sensor_info["wlansensor_info"]["ssid"] + "). "
            exit_msg += "Have to Quit."
            sys.exit(exit_msg)
    
    # Found a VALID CONNECTION in nmcli !!!!
    # Let's try to connect to the valid connection found in nmcli
    command_shell = ["sudo", "/usr/bin/nmcli", "connection", "up", sensor_info["wlansensor_info"]["ssid"]]
    try:
        p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    except:
        # Error trying to associate to the right SSID... HAVE TO QUIT
            localsyslog.critical("ConnectWLAN: Oh, oh... Not connected to "
                + "WLAN... "
                + "Even a valid connection in nmcli was found, to the right"
                + " SSID (" + sensor_info["wlansensor_info"]["ssid"] 
                + "). nmcli reported some SYSTEM ERROR."
                + "Could NOT connect with such SSID. "
                + "Have to quit.")
            localsyslog.debug("ConnectWLAN: The WLANsensor is NOT connected "
                + "to WLAN.")
            localsyslog.debug("ConnectWLAN: A valid connections were found in "
                + "nmcli, but could NOT connect to it. (SYSTEM ERROR)")

            localsyslog.info("ConnectWLAN: A valid connections were found in "
                + "nmcli, but could NOT connect to it. (SYSTEM ERROR)")
            localsyslog.info("ConnectWLAN: Please check WLAN connectivity.")
            localsyslog.debug("ConnectWLAN: Obviously have to quit...")
            
            localsyslog.error("WLAN Connection ERROR: " + str(sys.exc_info()[0]))
            localsyslog.error("WLAN Connection ERROR: " + str(sys.exc_info()[1]))
            
            # Update failures object and write to file
            failures["connectivity_failures"] += 1
            failure = {}
            failure["connfail_time"] = timestamp
            failure["connfail_code"] = 401
            failure["connfail_info"] = "A valid connection were found in nmcli, but could NOT connect to it."
            failure["connfail_order"] = len(failures["connectivity_failures_list"]) + 1
            failures["connectivity_failures_list"].append(failure)
            localsyslog.info("ConnectWLAN: Writing failures to sensorwatchdog"
                + " file...")
            WriteConnectivityFailuresFile(failures)
            
            exit_msg = "WLANsensor NOT connected to WLAN, FOUND a valid "
            exit_msg += "stored connection in nmcli, "
            exit_msg += "but a SYSTEM ERROR occurred. Could NOT connect the "
            exit_msg += "right SSID (" 
            exit_msg += sensor_info["wlansensor_info"]["ssid"] + "). "
            exit_msg += "Have to Quit."
            sys.exit(exit_msg)
        
    if not p1.returncode:
        # There was some error connecting with the right SSID
        # p1.returncode must be 0, if nmcli did it right... otherwise there was some error
        # Connectivity is not guarantee, so have to QUIT
        localsyslog.info("ConnectWLAN: nmcli reported an error connecting "
            + "with the right SSID. Have to QUIT...")
        localsyslog.critical("ConnectWLAN: nmcli reported error code: " 
            + p1.returncode)
        localsyslog.critical("ConnectWLAN: nmcli error info: " 
            + p1.stdout.decode("utf-8"))
        
        # Update failures object and write to file
        failures["connectivity_failures"] += 1
        failure = {}
        failure["connfail_time"] = timestamp
        failure["connfail_code"] = 403
        failure["connfail_info"] = "nmcli error info: " + p1.stdout.decode("utf-8")
        failure["connfail_order"] = len(failures["connectivity_failures_list"]) + 1
        failures["connectivity_failures_list"].append(failure)
        localsyslog.info("ConnectWLAN: Writing failures to sensorwatchdog"
            + " file...")
        WriteConnectivityFailuresFile(failures)
        
        exit_msg = "WLANsensor NOT connected to WLAN, FOUND a valid "
        exit_msg += "stored connection in nmcli, "
        exit_msg += "but nmcli reported an error connecting to the right SSID (" 
        exit_msg += sensor_info["wlansensor_info"]["ssid"] + "). "
        exit_msg += "Have to Quit."
        sys.exit(exit_msg)
    
    # Update failures object and write to file
    # As the sensor is connected to the right SSID, we can run the test
    # so failures must be reset.
    failures = {}
    failures["connectivity_failures"] = 0
    WriteConnectivityFailuresFile(failures)
    localsyslog.info("ConnectWLAN: sensor is connected to the right SSID...")
    localsyslog.info("ConnectWLAN: failures set to <0>, and written to "
        + "failures file: <" + failures_file + ">")
    
    return True


    
def ConnectWLANBand (sensor_info, wlaninfo, band="5G"):
    """
        Connects with the right SSID and Band
        returns updated wlaninfo
    """
    import subprocess
    import sys
    import time

    # Attach to Local SYSLOG
    localsyslog = logging.getLogger(logname)
    
    localsyslog.info("ConnectWLANBand: Connecting with the right Band <"
        + band + ">")
    
    # Reading failures file
    localsyslog.info("ConnectWLANBand: Reading failures from "
        + "sensorwatchdog file...")
    failures = ReadConnectivityFailuresFile()
    localsyslog.info("ConnectWLAN: Failures up to now: " 
        + str(failures["connectivity_failures"]))
        
    # We're connected to the right SSID, but need to change Band
    # let's get all the information about neighboring APs, including
    # the Virtual-APs of our SSID, using both bands
    localsyslog.info("ConnectWLANBand: Getting information of neighboring APs... ")
    command_shell = ["/usr/bin/nmcli", "-g",
        "SSID,BSSID,MODE,CHAN,FREQ,RATE,SIGNAL,SECURITY,WPA-FLAGS,RSN-FLAGS,DEVICE,ACTIVE",
        "dev", "wifi"
    ]
    try:
        p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        # Failure obtaining information to connect
        localsyslog.info("ConnectWLANBand: Can't get information from nmcli...")
        localsyslog.error("ConnectWLANBand ERROR: " + str(sys.exc_info()[0]))
        localsyslog.error("ConnectWLANBand ERROR: " + str(sys.exc_info()[1]))
        # Exits the program
        exit_msg = "WLANsensor (ConnectWLANBand) could NOT get information from nmcli... "
        exit_msg += "Have to Quit."
        sys.exit(exit_msg)
    
    
    # Let's get the MAC address in format AA-BB-CC-DD-EE-FF
    p2 = p1.stdout.decode("utf-8").replace("\\:","-").splitlines()
    vap_list = []
    keys = ["SSID","BSSID","MODE","CHAN","FREQ","RATE","SIGNAL","SECURITY",
        "WPA-FLAGS","RSN-FLAGS","DEVICE","ACTIVE"]
    
    localsyslog.info("ConnectWLANBand: Information from neighboring APs: "
        + "Success!!!")
    
    #Let place in the LIST vap_list all Virtual-AP
    for i,line in enumerate(p2):
        vap={}
        
        for i,(key,value) in enumerate(zip(keys,line.split(":"))):
            if i == 1:
                # Let's get back the MAC address format to AA:BB:CC:DD:EE:FF
                vap.update({key:value.replace("-",":")})
            elif i == 3:
                vap.update({key:int(value)})
            elif i == 6:
                vap.update({key:int(value)})
            else:
                vap.update({key:value})
        vap_list.append(vap.copy())
    
    localsyslog.info("ConnectWLANBand: Found <" + str(len(vap_list)) 
        + "> Virtual-APs...")
    localsyslog.info("ConnectWLANBand: List of Virtual-APs: "
        + str(vap_list))
    
    # Let's see how many are from the right SSID:
    ssid_vap_list = []
    for i,vap in enumerate(vap_list):
        if vap["SSID"] == sensor_info["wlansensor_info"]["ssid"]:
            ssid_vap_list.append(vap.copy())
    
    localsyslog.info("ConnectWLANBand: Found <" + str(len(ssid_vap_list))
        + "> Virtual-APs for SSID <" 
        + sensor_info["wlansensor_info"]["ssid"] + ">.")
    
    # Let's split Virtual-APs into two collections, one per Band
    band2g_vap_list = []
    band5g_vap_list = []
    for i,vap in enumerate(ssid_vap_list):
        if vap["FREQ"].startswith("2"):
            band2g_vap_list.append(vap.copy())
        elif vap["FREQ"].startswith("5"):
            band5g_vap_list.append(vap.copy())
    
    localsyslog.info("ConnectWLANBand: There are <"
        + str(len(band2g_vap_list)) + "> Virtual-APs in 2,4GHz Band and <"
        + str(len(band5g_vap_list)) + "> Virtual-APs in 5GHz Band.")
    
    # Let's select the best two VAP by SIGNAL power in order to connect to
    # one VAP per Band
    # the nmcli output, is ALREADY sorted by SIGNAL strength
    # So the first element [0] in each list is the best VAP to connect to
   
    if band == "2G":
        # The band passed to the function is 2G : 2,4GHz
        vap_selected = band2g_vap_list[0].copy()
    
    elif band == "5G":
        # The band passed to the function is 5G : 5GHz
        vap_selected = band5g_vap_list[0].copy()

    localsyslog.info("ConnectWLANBand: Selected Virtual-AP is <"
        + vap_selected["BSSID"] + ">, with SIGNAL level: "
        + str(vap_selected["SIGNAL"]) + "dBm")
    
    localsyslog.info("ConnectWLANBand: Connecting with the selected BSSID...")
    command_shell = ["sudo","/usr/bin/nmcli","connection","up",
            sensor_info["wlansensor_info"]["ssid"],
            "ap",vap_selected["BSSID"]
    ]
    try:
        p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    except:
        # Failure connecting to Virtual-AP
        localsyslog.info("ConnectWLANBand: Can't connect with the right Virtual-AP...")
        localsyslog.error("ConnectWLANBand: Failed trying to connect with SSID <"
            + sensor_info["wlansensor_info"]["ssid"] + ">, with AP <"
            + vap_bssid + ">, in Band <" + band + ">" )
        localsyslog.error("ConnectWLANBand ERROR: " + str(sys.exc_info()[0]))
        localsyslog.error("ConnectWLANBand ERROR: " + str(sys.exc_info()[1]))
        localsyslog.error("ConnectWLANBand ERROR: " + p1.stdout.decode("utf-8"))
        # Exits the program
        exit_msg = "WLANsensor (ConnectWLANBand) could NOT get information from nmcli... "
        exit_msg += "Have to Quit."
        sys.exit(exit_msg)
    
    
    localsyslog.info("ConnectWLANBand: Success!!!. Connected with BSSID:"
        + vap_selected["BSSID"])
        
    time.sleep(1)
    

    
def CheckWLANConnection (sensor_info):
    """ Check the WLAN association and WLAN IPaddress
        returns wlaninfo if successfully associated and IP
        returns False if not associated with the right SSID
        
        wlaninfo is a dict with all the information gathered from WLAN
    """
    import subprocess
    import sys

    # Attach to Local SYSLOG
    localsyslog = logging.getLogger(logname)
    
    #command_shell = "/sbin/iw dev | /usr/bin/awk '/Interface/ {print $2}'"
    # The output of this command is wlp1s0
    
    # The FULL output of /sbin/iw
    """
    sensor$ iw dev 
    phy#0
        Unnamed/non-netdev interface
                wdev 0x2
                addr f8:63:3f:28:05:e2
                type P2P-device
                txpower 0.00 dBm
        Interface wlp58s0
                ifindex 3
                wdev 0x1
                addr f8:63:3f:28:05:e1
                type managed
                channel 11 (2462 MHz), width: 20 MHz, center1: 2462 MHz
                txpower 22.00 dBm
    """
    
    # If not connected
    """
    sensor$ iw dev
    phy#0
        Unnamed/non-netdev interface
	        wdev 0x2
	        addr f8:63:3f:28:05:e2
	        type P2P-device
	        txpower 0.00 dBm
        Interface wlp58s0
	        ifindex 3
	        wdev 0x1
	        addr f8:63:3f:28:05:e1
	        type managed
	        txpower 0.00 dBm

    """
    # We are interested in:
    # Interface, HWaddr, Channel, width, txpower
    localsyslog.info("CheckWLANConnection: Getting wlan device...")
    command_shell = ["/sbin/iw","dev"]
    p1 = subprocess.run(command_shell, stdout=subprocess.PIPE)
    
    # We are interested only in the last part, from >Interface< to the end
    # so let's split the output and keep the last part:
    p2 = p1.stdout.decode("utf-8").partition("Interface ")[2]

    """
    p1.stdout.decode("utf-8").partition("Interface ") returns a triple with:
    0) the text from beginning to "Interface "
    1) "Interface" itself
    2) from "Interface"to the end
    We'll keep the 3rd part:
     wlp58s0
                ifindex 3
                wdev 0x1
                addr f8:63:3f:28:05:e1
                type managed
                channel 11 (2462 MHz), width: 20 MHz, center1: 2462 MHz
                txpower 22.00 dBm
    """
    
    # Let's convert the full text into lines
    output = p2.splitlines()
    
    # The first line has the most important part,the "dev"
    #
    # wlaninfo is a JSON object that will store all the information about the
    # WLAN connection
    wlaninfo = {}
    wlaninfo["dev"] = output[0].strip()
    
    localsyslog.info("CheckWLANConnection: WLAN interface: " + wlaninfo["dev"])
    
    for line in output:
        # Remove the TAB '\t' and check the starting string
        if line.lstrip('\t').startswith("addr"):
            wlaninfo["MACaddr"] = line.split()[1]
        elif line.lstrip('\t').startswith("channel"):
            wlaninfo["channel"] = line.split()[1].strip()
            wlaninfo["width"] = line.split()[5].strip()
            wlaninfo["Freq"] = line.split()[2].strip("(")
            wlaninfo["CenterFreq"] = line.split()[8].strip()
            if wlaninfo["Freq"].startswith("2"):
                wlaninfo["Band"] = "2G"
            elif wlaninfo["Freq"].startswith("5"):
                wlaninfo["Band"] = "5G"
        elif line.lstrip('\t').startswith("txpower"):
            wlaninfo["txpower"] = line.split()[1].strip()
    
    """
    Now let's focus on /sbin/iw dev <wlpXsY> link
    
    sensor$ iw dev wlp1s0 link
    Connected to 18:64:72:ea:f0:e4 (on wlp1s0)
        SSID: Temp
        freq: 2462
        RX: 4492337 bytes (28221 packets)
        TX: 5102104 bytes (25193 packets)
        signal: -17 dBm
        tx bitrate: 144.4 MBit/s MCS 15 short GI

        bss flags:      short-preamble short-slot-time
        dtim period:    1
        beacon int:     100
    """
    
    """
    If NOT connected:
    sensor$ iw dev wlp1s0 link
    Not connected.
    """
    command_shell = ["/sbin/iw","dev",wlaninfo["dev"],"link"]
    localsyslog.info("CheckWLANConnection: Checking if connected to WLAN...")
    p1 = subprocess.run(command_shell, stdout=subprocess.PIPE)
    p2 = p1.stdout.decode("utf-8").splitlines()
    
    # Let's see if we're connected to WLAN
    if p2[0].split()[0] == "Not":
        # We are NOT connected to WLAN... let's try to connect...
        connected = ConnectWLAN(sensor_info, wlaninfo)
    
    localsyslog.info("CheckWLANConnection: Connected to WLAN...")
        
    # Let's get the Virtual-AP we are connected to
    # which is the first line of p2, that is p2[0]
    # so split the line into words and choose the
    # Virtual-AP MAC address, the 3rd item, that is, [2]
    for line in p2:
        if line.lstrip('\t').startswith("Connected"):
            wlaninfo["Virtual-AP"] = line.split()[2]
        elif line.lstrip('\t').startswith("SSID"):
            wlaninfo["SSID"] = line.split()[1]
        elif line.lstrip('\t').startswith("signal"):
            wlaninfo["signal"] = line.split()[1]
        elif line.lstrip('\t').startswith("tx"):
            wlaninfo["tx_bitrate"] = line.split()[2]
            wlaninfo["MCS"] = line.split()[5]
        elif line.lstrip('\t').startswith("dtim"):
            wlaninfo["dtim"] = line.split()[2]
        elif line.lstrip('\t').startswith("beacon"):
            wlaninfo["beacon"] = line.split()[2]
            
    # Check if the SSID is the right one
    localsyslog.info("CheckWLANConnection: Check if WLANsensor is connected "
        + "to the right SSID...")
    if wlaninfo["SSID"] != sensor_info["wlansensor_info"]["ssid"]:
        # We're not in expected SSID... let's try to connect...
        connected = ConnectWLAN(sensor_info, wlaninfo)
        
    
    localsyslog.info("CheckWLANConnection: Perfect !!! - WLANsensor is "
        + "connected to SSID <" + wlaninfo["SSID"] + ">")
    
    localsyslog.info("CheckWLANConnection: Connection information...")
    localsyslog.info("CheckWLANConnection: Virtual-AP: <"
        + wlaninfo["Virtual-AP"] + ">")
    localsyslog.info("CheckWLANConnection: signal: <"
        + wlaninfo["signal"] + ">")
    localsyslog.info("CheckWLANConnection: Channel: <"
        + wlaninfo["channel"] + ">")
    localsyslog.info("CheckWLANConnection: Frequency: <"
        + wlaninfo["Freq"] + ">")
    
    # Let's see which band to use:
    w_info = sensor_info["wlansensor_info"]
    if w_info["test_band_use"] == "Rotating":
        # There is a configuration number of followed test in one band
        # before changing to the other band
        if w_info["test_band_rotating_rounds_current"] > w_info["test_band_rotating_rounds"]:
            # Have to change the band
            # This is the first Test in the new band
            sensor_info["wlansensor_info"]["test_band_rotating_rounds_current"] = 1
            
            if w_info["test_band_last_use"] == "2G":
                # Next round of tests must use 5G band
                connected = ConnectWLANBand(sensor_info, wlaninfo, "2G")
            
            elif w_info["test_band_last_use"] == "5G":
                # Next round of tests must use 2G band
                connected = ConnectWLANBand(sensor_info, wlaninfo, "5G")
        
        else:
            # Have to continue in the same band than previous tests
            # Increase the counter
            sensor_info["wlansensor_info"]["test_band_rotating_rounds_current"] += 1
            connected = ConnectWLANBand(sensor_info, wlaninfo, w_info["test_band_last_use"])
            
            
    elif w_info["test_band_use"] == "2G":
        # Always use 2G band
        connected = ConnectWLANBand(sensor_info, wlaninfo, "2G")
        
    elif w_info["test_band_use"] == "5G":
        # Always use 5G band
        connected = ConnectWLANBand(sensor_info, wlaninfo, "5G")
        
    elif w_info["test_band_use"] == "Random":
        # Random Band selection for test
        random_band = random.choice(w_info["test_band_allowed"])
        connected = ConnectWLANBand(sensor_info, wlaninfo, random_band)
        
    
    # Update failures object and write to file
    # As the sensor is connected to the right SSID, we can run the test
    # so failures must be reset.
    failures = {}
    failures["connectivity_failures"] = 0
    WriteConnectivityFailuresFile(failures)
    localsyslog.info("CheckWLANConnection: sensor is connected to the "
        + "right SSID...")
    localsyslog.info("CheckWLANConnection: failures set to <0>, and written to "
        + "failures file: <" + failures_file + ">")
        

    return wlaninfo


    
    
def SyslogInitialization (sensor_name, syslog_server="192.168.1.54", syslog_UDP_port=514): 

    import logging
    from logging.handlers import SysLogHandler
	
    # Create the logger for remote SYSLOG, that is the SPLUNK receiver
    logger = logging.getLogger(sensor_name)
    logger.setLevel(logging.DEBUG)

    # Attach to Local SYSLOG
    localsyslog = logging.getLogger(logname)
    
    # Let's check the connectivity and inform to local syslog
    IPconnect = CheckIPConnection(syslog_server)
    if IPconnect:
        localsyslog.info("Connectivity with syslog remote Receiver <"
            + syslog_server + "> OK.")
    else:
        localsyslog.info("Connectivity with syslog remote Receiver <"
            + syslog_server + "> FAILED.")
        localsyslog.info("Continuing, as it's UDP and could be a temporary "
            + "problem")


   # Creamos el controlador (handler) indicando la IP y el PUERTO
    udp = logging.handlers.SysLogHandler(address=(syslog_server, syslog_UDP_port))
    # Mandamos todo el logging
    udp.setLevel(logging.DEBUG)

    # Formato del mensaje a enviar
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -'
        + '%(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    udp.setFormatter(formatter)

    # Bind the syslog handler with the logger
    logger.addHandler(udp)

    #logger.info('Antes de return')

    localsyslog.info("Remote syslog server <" + syslog_server + "> Initialization SUCCESS")   
 
    return logger


def LocalSyslogInitialization (logname):

    import logging
    from logging.handlers import SysLogHandler

    # Create the logger
    logger = logging.getLogger(logname)
    logger.setLevel(logging.DEBUG)

    # Create the handler for LOCAL syslog
    # facility=17 means 
    #  other codes through 15 reserved for system use
    LOG_LOCAL0    = 16      #  reserved for local use
    LOG_LOCAL1    = 17      #  reserved for local use
    LOG_LOCAL2    = 18      #  reserved for local use
    LOG_LOCAL3    = 19      #  reserved for local use
    LOG_LOCAL4    = 20      #  reserved for local use
    LOG_LOCAL5    = 21      #  reserved for local use
    LOG_LOCAL6    = 22      #  reserved for local use
    LOG_LOCAL7    = 23      #  reserved for local use
    localsyslog = logging.handlers.SysLogHandler(address='/dev/log', facility=LOG_LOCAL1)
    # Mandamos todo el logging
    localsyslog.setLevel(logging.DEBUG)


    # Formats the Local Syslog message
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    localsyslog.setFormatter(formatter)

    # Bind the syslog handler with the logger
    logger.addHandler(localsyslog)

    # Test
    logger.info('Local syslog Initializated.')
    
    return logger


def MongoConnection (mongo_server = "192.168.1.5", mongo_port = 27017):

    from pymongo import MongoClient

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    if not CheckIPConnection(mongo_server):
        localsyslog.error("MongoDB server: "
            + mongo_server + " not ping reachable... "
            + "Creating the MongoDB Client handler in any case.")

    # Set the MongoDB params
    mongo_url = "mongodb://" + mongo_server + ":" + str(mongo_port)
    # Connection with MongoDB server
    mongoclient = MongoClient(mongo_url)

    return mongoclient


def SelectMongoDB(mongoclient, dbname):
    
    from pymongo.errors import ConnectionFailure
    import sys

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)
    
    try:
        # The ismaster command is cheap and does not require auth.
        mongoclient.admin.command('ismaster')
        # Connect with the right DB name in MongoDB server
        mongodb = mongoclient[dbname]
        localsyslog.info("DB "
            + dbname + " successfully selected in MongoDB server.")
        return mongodb

    except ConnectionFailure:
        localsyslog.error("DB "
            + dbname + " could NOT be addressed in MongoDB server.")
        localsyslog.error("pymongo: " + str(sys.exc_info()[0]))
        localsyslog.error("pymongo: " + str(sys.exc_info()[1]))
        localsyslog.debug("Check MongoDB server, connectivity, DB name, etc.")
        localsyslog.debug("pymongo: " + str(sys.exc_info()[0]))
        localsyslog.debug("pymongo: " + str(sys.exc_info()[1]))
        return False


        
def SelectMongodbCollection(mongodb, collection):
    
    from pymongo.errors import ConnectionFailure
    import sys

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    if not mongodb:
        # No pointer to MongoDB, as there was an error creating the DB
        # in the MoongoDB server
        localsyslog.error("MongoDB: There was a problen creating"
            + "database, so can't access Collections in the database")
        localsyslog.error("MongoDB: skipping MongoDB insertions...")
        return False

    try:
        mongodb.collection_names()
        #print(mongodb.collection_names())
        mongocollection = mongodb[collection]
        localsyslog.info("Collection " + collection 
            + " successfully selected in DB")
        return mongocollection

    except ConnectionFailure:
        localsyslog.error("ERROR: Could not select collection " 
            + collection + "in the DB")
        localsyslog.debug("Check MongoDB server, connectivity, DB and Collections...")
        return False

        
def UpdateMongodbSensorInfo(sensors, sensor_info):

    from pymongo.errors import ConnectionFailure
    
    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    if not sensors:
        # No pointer to Collection sensors, basically because MongoDB Server
        # was down during connection stage
        localsyslog.error("MongoDB: There was a problem updating sensor"
            + "information.")
        localsyslog.error("MongoDB: There is no pointer to Collection."
            + "Most probaly error, MongoDB server is down in Connection stage.")
        localsyslog.error("MongoDB: skipping MongoDB insertions...")
        return False

    sensor_id = sensor_info["wlansensor_info"]["sensor_id"]
    
    try:
        # try to get the collection name, if fails, there is a connectivity issue
        sensors.name
        
        # Connection success
        localsyslog.info("Connected to <sensors> collection for update...")
        # Let's check if the sensor is already in the Collection
        if sensors.count({ "wlansensor_info.sensor_id" : sensor_id }) >= 1:
            # sensor_id IS IN the Collection, so let's update
            # Update information
            localsyslog.info("SENSOR already defined in the Collection.")
            localsyslog.info("Let's update the timestamp for the last connection")
            result = sensors.update_one(
                {"wlansensor_info.sensor_id":sensor_id},
                {"$set":
                    {"wlansensor_info.lastconnection": 
                        sensor_info["wlansensor_info"]["lastconnection"]
                    }
                })        
            localsyslog.info("SENSOR information updated in Collection.")

        else :
            # sensor_id IS NOT PRESENT in the Collection...
            # Creates the sensor information for the first time
            localsyslog.info("Creating the SENSOR... "
                + "sensor_id was not present in Collection")
            result = sensors.insert_one(sensor_info).inserted_id
            localsyslog.info("SENSOR created in Collection.")
        return result
        
    except ConnectionFailure:
        localsyslog.error("ERROR: Could not select collection " 
            + "<sensors> in the DB for updating/creating sensor_id: "
            + sensor_id)
        localsyslog.debug("Check MongoDB server, connectivity, DB and Collections...")
        return False

    
    
def WriteMongodbAnalytics(analytic, testresult):


    from pymongo.errors import ConnectionFailure

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    """
        analytic = {
            "mongodb_ip":"192.168.1.5",
            "mongodb_port":27017,
            "mongodb_name":"Local",
            "mongodb_db":"AENA",
            "mongodb_available": True,
            "mongodb_analyticshandler": <object to mongo client pointing to the collection>
        }
        
    """
    
    if analytic["mongodb_available"]:
        # All OK, mongodb collection is available (or it was)
        try:
            # The ismaster command is cheap and does not require auth.
            analytic["mongodb_analyticshandler"].name
            insert_id = analytic["mongodb_analyticshandler"].insert_one(testresult).inserted_id
            localsyslog.info("WriteMongodbAnalytics: Analytics " + str(testresult) 
                + "successfully inserted into MongoDB server <"
                + analytic["mongodb_name"] + "> (" + analytic["mongodb_ip"] + ")")
            return insert_id
    
        except ConnectionFailure:
            localsyslog.error("WriteMongodbAnalytics ERROR: Could not insert analytics into MongoDB server <"
                + analytic["mongodb_name"] + "> (" + analytic["mongodb_ip"] + "), Database name <"
                + analytic["mongodb_db"] + ">, Collection <analytics>.")
            localsyslog.debug("Check MongoDB server, "
                + "connectivity, DB, collections, etc.")
            return False
    
    else:
        # No pointer to Collection analytics, basically because MongoDB Server
        # was down during connection stage
        localsyslog.error("WriteMongodbAnalytics: There was a problem updating analytics information with "
            + "server <" + analytic["mongodb_name"] + "> (" + analytic["mongodb_ip"] + "), Database name <"
            + analytic["mongodb_db"] + ">, Collection <analytics>.")
        localsyslog.error("WriteMongodbAnalytics: There is no pointer to Collection."
            + "Most probaly error, MongoDB server is down during Connection stage.")
        localsyslog.error("WriteMongodbAnalytics: skipping MongoDB insertions...")
        return False


def ConnectInfluxDB (sensor_info):
    """
        Let's connect with the InfluxDB to store the measurements
    """
    from influxdb import InfluxDBClient
    from influxdb.exceptions import InfluxDBClientError
    import sys

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    localsyslog.info("ConnectInfluxDB: Connecting with <"
        + str(len(sensor_info["wlansensor_info"]["influxdb_servers"]))
        + "> InfluxDB servers")

    influxdbclients=[]
    for i, element in enumerate(sensor_info["wlansensor_info"]["influxdb_servers"]):
        
        influxdb_client = element.copy()
        
        localsyslog.info("ConnectInfluxDB: Connecting with InfluxDB server <"
            + element["influxdb_name"]
            + "> with IP/TCP: " + element["influxdb_ip"]
            + "/" + str(element["influxdb_port"]))

        # Check IP ping with InfluxDB Server
        localsyslog.info("ConnectInfluxDB: Checking IP connectivity with InfluxDB server: "
            + element["influxdb_ip"])
        if not CheckIPConnection(element["influxdb_ip"]):
            localsyslog.error("ConnectInfluxDB: InfluxDB server <"
                + element["influxdb_ip"] + "> not ping reachable... "
                + "Creating the InfluxDB Client handler in any case.")
        else:
            localsyslog.info("ConnectInfluxDB: IP connectivity OK...")
            
        influxdb_client["influxdbhandler"] = InfluxDBClient(
            element["influxdb_ip"], 
            element["influxdb_port"],
            element["influxdb_user"],
            element["influxdb_passwd"],
            element["influxdb_db"])

        # Connecting with InfluxDB Server and select or create the DB
        # here is where connectity problems may appear...
        try:
            influxdb_client["influxdbhandler"].create_database(element["influxdb_db"])
            influxdbclients.append(influxdb_client.copy())
            
            """
            influxclients = [
                {
                    "influxdb_ip":"192.168.1.5",
                    "influxdb_port":8086,
                    "influxdb_name":"Local",
                    "influxdb_user":"aena",
                    "influxdb_passwd":"aena",
                    "influxdb_db":"AENA",
                    "influxdbhandler": {Object to InfluxDB client}
                }
            ]
            """
            
            localsyslog.info("ConnectInfluxDB: Database " + element["influxdb_db"]
                + " SUCCESSFULLY created in InfluxDB server: "
                + element["influxdb_ip"])
            return influxdbclients

        #except InfluxDBClientError:
        except:
            localsyslog.error("ConnectInfluxDB ERROR:  Failure creating DB " 
                + element["influxdb_db"] + " in InfluxDB server: " 
                + element["influxdb_ip"])
            localsyslog.error("ConnectInfluxDB ERROR: " + str(sys.exc_info()[0]))
            localsyslog.error("ConnectInfluxDB ERROR: " + str(sys.exc_info()[1]))
            localsyslog.debug("ConnectInfluxDB ERROR: Error creating database <"
                + element["influxdb_db"] + "> in InfluxDB Server <"
                + element["influxdb_ip"] + ">. Please check connectivity "
                + "with InfluxDB Server")
            
            return False




def RunIperf3Tests(sensor_info):
    """
        Let's run the iperf3 tests with the servers from sensor_info
    """
    import subprocess
    import time
    import json

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    localsyslog.info("RunIperf3Tests: Starting iperf3 tests with "
        + str(len(sensor_info["wlansensor_info"]["test_servers"]))
        + " test servers")

    # Let's PING the TEST SERVERS, for ARP and DNS resolution and cache
    localsyslog.info("RunIperf3Tests: Will now ping test servers for caching MAC and DNS... "
        + "avoiding false results...")
    
    iperf3_servers = sensor_info["wlansensor_info"]["test_servers"].copy()

    for iperf3_server in iperf3_servers:
    
        iperf3_server["tcp_test"] = {}
        if not CheckIPConnection(iperf3_server["test_server_ip"]):
            # Not reachable... skip this server from tests
            localsyslog.error("RunIperf3Tests ERROR: Test Server: <"
                + iperf3_server["test_server_ip"] + "> is NOT reachable. Will be skipped from TCP tests.")
            iperf3_server["tcp_test"]["available"] = False
        else:
            # Ping success, now it must be in ARP table
            localsyslog.info("RunIperf3Tests: Test Server: <"
                + iperf3_server["test_server_ip"] + "> is now in ARP/DNS cache.")
            iperf3_server["tcp_test"]["available"] = True

            localsyslog.info("RunIperf3Tests: Running the TCP tests...")

            command_shell = [
                "/usr/bin/iperf3",
                "--client", iperf3_server["test_server_ip"],
                "--port",  iperf3_server["test_server_port"],
                "--json"
            ]
            p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            timestamp_influxdb = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())
                        
            if p1.returncode:
                # Server down, unreachable
                localsyslog.error("RunIperf3Tests ERROR: TCP Test failure with Test Server <"
                    + iperf3_server["test_server_ip"] + ">. Not reachable for testing...")
                localsyslog.debug("RunIperf3Tests ERROR: " + p1.stdout.decode("utf-8"))
                iperf3_server["tcp_test"]["available"] = False
                
            else:
                # UDP Test SUCCESS !!!!
                localsyslog.info("RunIperf3Tests: TCP Test with server <" + iperf3_server["test_server_ip"]
                    + "> successfully done.")
                
                j1 = json.loads(p1.stdout.decode("utf-8"))
                iperf3_server["tcp_test"].update(j1["end"]["streams"][0]["sender"])
                iperf3_server["tcp_test"]["timestamp"] = timestamp
                iperf3_server["tcp_test"]["timestamp_influxdb"] = timestamp_influxdb
                
                """
                    iperf3_server = [
                        {
                            "test_server_ip": "192.168.1.54",
                            "test_server_port": 5201,
                            "test_server_name": "Local - iperf3 Local",
                            "test_server_udp_bandwidth":"10M",
                            "test_server_udp_time": "10",
                            "test_server_interval": "10",
                            "tcp_test": {
                                "available": True,
                                "timestamp": "2017-12-28 18:43:17",
                                "socket": 4,
                                "start": 0,
                                "end": 10.000525,
                                "seconds": 10.000525,
                                "bytes": 444473728,
                                "bits_per_second": 355560315.564814,
                                "retransmits": 0,
                                "max_snd_cwnd": 3075552,
                                "max_rtt": 14185,
                                "min_rtt": 5595,
                                "mean_rtt": 9152
                            }
                        }
                    ]
                """
                
                localsyslog.info("RunIperf3Tests: TCP measurements..." + str(iperf3_server))

    return iperf3_servers                

"""
iperf3 TCP output
{
    "start": {
        "connected": [
            {
                "socket": 4,
                "local_host": "192.168.1.4",
                "local_port": 55272,
                "remote_host": "192.168.1.5",
                "remote_port": 5201
            }
        ],
        "version": "iperf 3.1.3",
        "system_info": "Linux nuc-i3 4.13.0-21-generic #24-Ubuntu SMP Mon Dec 18 17:29:16 UTC 2017 x86_64",
        "timestamp": {
            "time": "Thu, 28 Dec 2017 17:18:33 GMT",
            "timesecs": 1514481513
        },
        "connecting_to": {
            "host": "192.168.1.5",
            "port": 5201
        },
        "cookie": "nuc-i3.1514481513.733938.4a9f820408d",
        "tcp_mss_default": 1448,
        "test_start": {
            "protocol": "TCP",
            "num_streams": 1,
            "blksize": 131072,
            "omit": 0,
            "duration": 10,
            "bytes": 0,
            "blocks": 0,
            "reverse": 0
        }
    },
    "intervals": [
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 0,
                    "end": 1.000214,
                    "seconds": 1.000214,
                    "bytes": 37772528,
                    "bits_per_second": 302115541.097686,
                    "retransmits": 0,
                    "snd_cwnd": 1023736,
                    "rtt": 8093,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 0,
                "end": 1.000214,
                "seconds": 1.000214,
                "bytes": 37772528,
                "bits_per_second": 302115541.097686,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 1.000214,
                    "end": 2.000407,
                    "seconds": 1.000193,
                    "bytes": 41311440,
                    "bits_per_second": 330427786.880134,
                    "retransmits": 0,
                    "snd_cwnd": 1911360,
                    "rtt": 7188,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 1.000214,
                "end": 2.000407,
                "seconds": 1.000193,
                "bytes": 41311440,
                "bits_per_second": 330427786.880134,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 2.000407,
                    "end": 3.000568,
                    "seconds": 1.000161,
                    "bytes": 44504280,
                    "bits_per_second": 355976866.866817,
                    "retransmits": 0,
                    "snd_cwnd": 2248744,
                    "rtt": 5595,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 2.000407,
                "end": 3.000568,
                "seconds": 1.000161,
                "bytes": 44504280,
                "bits_per_second": 355976866.866817,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 3.000568,
                    "end": 4.000605,
                    "seconds": 1.000037,
                    "bytes": 44504280,
                    "bits_per_second": 356021083.283675,
                    "retransmits": 0,
                    "snd_cwnd": 2373272,
                    "rtt": 8570,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 3.000568,
                "end": 4.000605,
                "seconds": 1.000037,
                "bytes": 44504280,
                "bits_per_second": 356021083.283675,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 4.000605,
                    "end": 5.000679,
                    "seconds": 1.000074,
                    "bytes": 45807480,
                    "bits_per_second": 366432757.043046,
                    "retransmits": 0,
                    "snd_cwnd": 2494904,
                    "rtt": 14185,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 4.000605,
                "end": 5.000679,
                "seconds": 1.000074,
                "bytes": 45807480,
                "bits_per_second": 366432757.043046,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 5.000679,
                    "end": 6.000193,
                    "seconds": 0.999514,
                    "bytes": 44699760,
                    "bits_per_second": 357771920.325743,
                    "retransmits": 0,
                    "snd_cwnd": 2785952,
                    "rtt": 7220,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 5.000679,
                "end": 6.000193,
                "seconds": 0.999514,
                "bytes": 44699760,
                "bits_per_second": 357771920.325743,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 6.000193,
                    "end": 7.000249,
                    "seconds": 1.000056,
                    "bytes": 46002960,
                    "bits_per_second": 368003061.389755,
                    "retransmits": 0,
                    "snd_cwnd": 2929304,
                    "rtt": 10117,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 6.000193,
                "end": 7.000249,
                "seconds": 1.000056,
                "bytes": 46002960,
                "bits_per_second": 368003061.389755,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 7.000249,
                    "end": 8.000553,
                    "seconds": 1.000304,
                    "bytes": 47110680,
                    "bits_per_second": 376770907.789785,
                    "retransmits": 0,
                    "snd_cwnd": 2929304,
                    "rtt": 10614,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 7.000249,
                "end": 8.000553,
                "seconds": 1.000304,
                "bytes": 47110680,
                "bits_per_second": 376770907.789785,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 8.000553,
                    "end": 9.000605,
                    "seconds": 1.000052,
                    "bytes": 47160840,
                    "bits_per_second": 377267111.447474,
                    "retransmits": 0,
                    "snd_cwnd": 2929304,
                    "rtt": 11008,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 8.000553,
                "end": 9.000605,
                "seconds": 1.000052,
                "bytes": 47160840,
                "bits_per_second": 377267111.447474,
                "retransmits": 0,
                "omitted": false
            }
        },
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 9.000605,
                    "end": 10.000525,
                    "seconds": 0.99992,
                    "bytes": 45599480,
                    "bits_per_second": 364825065.640787,
                    "retransmits": 0,
                    "snd_cwnd": 3075552,
                    "rtt": 8930,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 9.000605,
                "end": 10.000525,
                "seconds": 0.99992,
                "bytes": 45599480,
                "bits_per_second": 364825065.640787,
                "retransmits": 0,
                "omitted": false
            }
        }
    ],
    "end": {
        "streams": [
            {
                "sender": {
                    "socket": 4,
                    "start": 0,
                    "end": 10.000525,
                    "seconds": 10.000525,
                    "bytes": 444473728,
                    "bits_per_second": 355560315.564814,
                    "retransmits": 0,
                    "max_snd_cwnd": 3075552,
                    "max_rtt": 14185,
                    "min_rtt": 5595,
                    "mean_rtt": 9152
                },
                "receiver": {
                    "socket": 4,
                    "start": 0,
                    "end": 10.000525,
                    "seconds": 10.000525,
                    "bytes": 440648112,
                    "bits_per_second": 352499983.431551
                }
            }
        ],
        "sum_sent": {
            "start": 0,
            "end": 10.000525,
            "seconds": 10.000525,
            "bytes": 444473728,
            "bits_per_second": 355560315.564814,
            "retransmits": 0
        },
        "sum_received": {
            "start": 0,
            "end": 10.000525,
            "seconds": 10.000525,
            "bytes": 440648112,
            "bits_per_second": 352499983.431551
        },
        "cpu_utilization_percent": {
            "host_total": 2.378981,
            "host_user": 0.181259,
            "host_system": 2.197723,
            "remote_total": 0.120835,
            "remote_user": 9.6e-05,
            "remote_system": 0.120739
        }
    }
}
"""
               
    
def RunDelayTests(sensor_info):
    """
        Let's run the delay tests with the servers from sensor_info
        Using ping for round-trip time delay
    """
    import subprocess
    import time
    import json

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)
    localsyslog.info("Starting Delay tests with "
        + str(len(sensor_info["wlansensor_info"]["test_servers"]))
        + " test servers...")
    
    """
    #########################################################################
    # ARP CACHE, in case of need
    #########################################################################
    # As iperf3 tests have been already done, it's expected that there is no need for
    # ARP resolution, as the IP-MAC of the destination is cached.
    # It's important, as may introduce some additional delay
    # In any case let's chek if MACs have been cached
    localsyslog.info("RunDelayTests: Reading ARP table...")
    command_shell = ["/sbin/ip", "neigh"]
    p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Output of ip neigh
    # 192.168.1.2 dev wlp1s0 lladdr e8:e7:32:51:6e:14 STALE
    # 192.168.1.100 dev wlp1s0 lladdr bc:ae:c5:16:33:a5 DELAY
    # 192.168.1.1 dev wlp1s0 lladdr 38:72:c0:29:03:d4 STALE
    
    if not p1.returncode:
        # There was some SYSTEM problem... don't have information about ARP
        localsyslog.error("Problem trying to get ARP table (ip neigh), will follow in any case...")
    
    # Let's use the output as a single string, and look for the TEST-SERVERS IP Addresses
    p2 = p1.stdout.decode("utf-8")
    
    delay_servers = sensor_info["wlansensor_info"]["test_servers"].copy()
    
    localsyslog.info("RunDelayTests: Checking if Test Servers IPs are in ARP Table...")
    for i,test_server in enumerate(sensor_info["wlansensor_info"]["test_servers"]):
        # Let's find the TEST SERVERS in the ARP
        if not p2.find(test_server["test_server_ip"]):
            # NOT FOUND !!! The IP address is NOT in ARP table
            localsyslog.error("RunDelayTests ERROR: Test Server: <" 
                + test_server["test_server_ip"] + "> not in ARP Table... Will ping it to cache in ARP.")
            # let's ping the server...
            if not CheckIPConnection(test_server["test_server_ip"]):
                # Not reachable... skip this server from tests
                localsyslog.error("RunDelayTests ERROR: Test Server: <"
                    + test_server["test_server_ip"] + "> is NOT reachable. Will be skipped from delay tests.")
                delay_servers[i]["AVAILABLE"] = False
            else:
                # Ping success, now it must be in ARP table
                localsyslog.info("RunDelayTests: Test Server: <"
                    + test_server["test_server_ip"] + "> is now in ARP Table.")
                delay_servers[i]["AVAILABLE"] = True
        else:
            # IP in in ARP table
            localsyslog.info("RunDelayTests: Test Server <"
                + test_server["test_server_ip"] + "> is in ARP Table.")
            delay_servers[i]["AVAILABLE"] = True
    """
    # Let's PING the TEST SERVERS, for ARP and DNS resolution and cache
    localsyslog.info("RunDelayTests: Will now ping test servers for caching MAC and DNS... "
        + "avoiding false results...")
    
    delay_servers = sensor_info["wlansensor_info"]["test_servers"].copy()
    """
        delay_servers = [
            {
                "test_server_ip": "192.168.1.54",
                "test_server_port": 5201,
                "test_server_name": "Local - iperf3 Local",
                "test_server_udp_bandwidth":"10M",
                "test_server_udp_time": "10",
                "test_server_interval": "10"
            }
        ]
    """
    for delay_server in delay_servers:
        delay_server["delay_test"] = {}
        if not CheckIPConnection(delay_server["test_server_ip"]):
            # Not reachable... skip this server from tests
            localsyslog.error("RunDelayTests ERROR: Test Server: <"
                + delay_server["test_server_ip"] + "> is NOT reachable. Will be skipped from delay tests.")
            delay_server["delay_test"]["available"] = False
        else:
            # Ping success, now it must be in ARP table
            localsyslog.info("RunDelayTests: Test Server: <"
                + delay_server["test_server_ip"] + "> is now in ARP/DNS cache.")
            delay_server["delay_test"]["available"] = True
        
            """
            delay_servers = [
                {
                    "test_server_ip": "192.168.1.54",
                    "test_server_port": 5201,
                    "test_server_name": "Local - iperf3 Local",
                    "test_server_udp_bandwidth":"10M",
                    "test_server_udp_time": "10",
                    "test_server_interval": "10",
                    "available": True
                }
            ]
            """
            """
            # Now let's run the delay test...
            # using regular ping tool
            # For better accuracy, a NTP timestamped TCP flow, avoiding IP fragmentation, is preferred... 
            # but for now let's use ping
            # ping -A -q -c 20 <IPADDRESS>
                # -A        -> wait for echo response and send new packet, instead of default 1 second between packets
                # -q        -> run in quiet mode, reporting the statistics at the end
                # -c 20    -> send 20 echo request
            # Adding the results to the delay_servers list of dict:
            """

            
            localsyslog.info("RunDelayTests: Running the delay tests...")
    
            command_shell = ["/bin/ping", "-A", "-q", 
                "-c", delay_server["test_server_delay_packets"], 
                delay_server["test_server_ip"]
            ]
            p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            timestamp_influxdb = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())
            
            if p1.returncode:
                # Server down, unreachable
                localsyslog.error("RunDelayTests ERROR: Delay Test failure with Test Server <"
                    + delay_server["test_server_ip"] + ">. Not reachable for testing...")
                localsyslog.debug("RunDelayTests ERROR: " + p1.stdout.decode("utf-8"))
                
                delay_server["delay_test"]["available"] = False
                
            else:
                # Delay Test SUCCESS !!!!
                localsyslog.info("RunDelayTests: Delay Test with server <" + delay_server["test_server_ip"]
                    + "> successfully done.")
                """
                    Content of ping output  - p1.stdout.decode("utf-8")
                    [0]PING 192.168.1.54 (192.168.1.54) 56(84) bytes of data.
                    [1]
                    [2]--- 192.168.1.54 ping statistics ---
                    [3]20 packets transmitted, 20 received, 0% packet loss, time 3812ms
                    [4]rtt min/avg/max/mdev = 2.804/42.068/202.262/47.512 ms, pipe 2, ipg/ewma 200.652/32.505 ms
                """
                p2 = p1.stdout.decode("utf-8").splitlines()
                delay_server["delay_test"]["timestamp"] = timestamp
                delay_server["delay_test"]["timestamp_influxdb"] = timestamp_influxdb
                delay_server["delay_test"]["d_packets_sent"] = p2[3].split()[0]
                delay_server["delay_test"]["d_packets_received"] = p2[3].split()[3]
                delay_server["delay_test"]["d_packet_loss"] = str(int(p2[3].split()[0]) - int(p2[3].split()[3]))
                delay_server["delay_test"]["d_packet_loss_percent"] = float(p2[3].split()[5].strip("%"))
                delay_server["delay_test"]["d_time"] = p2[3].split()[9].strip("ms")
                delay_server["delay_test"]["d_rtt_min_ms"] = float(p2[4].split()[3].split("/")[0])
                delay_server["delay_test"]["d_rtt_avg_ms"] = float(p2[4].split()[3].split("/")[1])
                delay_server["delay_test"]["d_rtt_max_ms"] = float(p2[4].split()[3].split("/")[2])
                delay_server["delay_test"]["d_rtt_mdev_ms"] = float(p2[4].split()[3].split("/")[3])
                delay_server["delay_test"]["d_ipg_ms"] = float(p2[4].split()[len(p2[4].split())-2].split("/")[0])
                delay_server["delay_test"]["d_ewma_ms"] = float(p2[4].split()[len(p2[4].split())-2].split("/")[1])
                
                """
                delay_servers = [
                    {
                        "test_server_ip": "192.168.1.54",
                        "test_server_port": 5201,
                        "test_server_name": "Local - iperf3 Local",
                        "test_server_udp_bandwidth":"10M",
                        "test_server_udp_time": "10",
                        "test_server_interval": "10",
                        "delay_test": {
                            "available": True,
                            "timestamp": "Thu, 28 Dec 2017 16:16:52 GMT",
                            "d_packets_sent": "20",
                            "d_packets_received": "20",
                            "d_packet_loss": "0",
                            "d_packet_loss_percent": "0",
                            "d_time": "3812",
                            "d_rtt_min_ms": "2.804",
                            "d_rtt_avg_ms": "42.068",
                            "d_rtt_max_ms": "202.262",
                            "d_rtt_mdev_ms": "47.512",
                            "d_ipg_ms": "200.652",
                            "d_ewma_ms": "32.505"
                        }
                    }
                ]
                """
                
                localsyslog.info("RunDelayTests: Delay measurements..." + str(delay_server))

    return delay_servers
    
    

    
def RunUDPTests(sensor_info):
    """
        Let's run the UDP tests with the servers from sensor_info
        Using iperf3 for jitter and packet loss
    """
    import subprocess
    import time
    import json

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)
    localsyslog.info("RunUDPTests: Starting UDP tests with "
        + str(len(sensor_info["wlansensor_info"]["test_servers"]))
        + " test servers...")
    
    # Let's PING the TEST SERVERS, for ARP and DNS resolution and cache
    localsyslog.info("RunUDPTests: Will now ping test servers for caching MAC and DNS... "
        + "avoiding false results...")
    
    udp_servers = sensor_info["wlansensor_info"]["test_servers"].copy()

    """
        udp_servers = [
            {
                "test_server_ip": "192.168.1.54",
                "test_server_port": 5201,
                "test_server_name": "Local - iperf3 Local",
                "test_server_udp_bandwidth":"10M",
                "test_server_udp_time": "10",
                "test_server_interval": "10",
            }
        ]
    """
    
    for udp_server in udp_servers:
        udp_server["udp_test"] = {}
        if not CheckIPConnection(udp_server["test_server_ip"]):
            # Not reachable... skip this server from tests
            localsyslog.error("RunUDPTests ERROR: Test Server: <"
                + udp_server["test_server_ip"] + "> is NOT reachable. Will be skipped from UDP tests.")
            udp_server["udp_test"]["available"] = False
        else:
            # Ping success, now it must be in ARP table
            localsyslog.info("RunUDPTests: Test Server: <"
                + udp_server["test_server_ip"] + "> is now in ARP/DNS cache.")
            udp_server["udp_test"]["available"] = True

            localsyslog.info("RunUDPTests: Running the UDP tests...")
            
            command_shell = ["/usr/bin/iperf3",
                "--client", udp_server["test_server_ip"],
                "--udp",
                "--interval", udp_server["test_server_interval"],
                "--time", udp_server["test_server_udp_time"],
                "--bandwidth", udp_server["test_server_udp_bandwidth"],
                "--json"
            ]
            
            p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            timestamp_influxdb = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())
            
            if p1.returncode:
                # Server down, unreachable
                localsyslog.error("RunUDPTests ERROR: UDP Test failure with Test Server <"
                    + udp_server["test_server_ip"] + ">. Not reachable for testing...")
                localsyslog.debug("RunUDPTests ERROR: " + p1.stdout.decode("utf-8"))
                
                udp_server["udp_test"]["available"] = False

                
            else:
                # UDP Test SUCCESS !!!!
                localsyslog.info("RunUDPTests: UDP Test with server <" + udp_server["test_server_ip"]
                    + "> successfully done.")
                j1 = json.loads(p1.stdout.decode("utf-8"))
                udp_server["udp_test"].update(j1["end"]["streams"][0]["udp"])
                udp_server["udp_test"]["timestamp"] = timestamp
                udp_server["udp_test"]["timestamp_influxdb"] = timestamp_influxdb
    """
        udp_servers = [
            {
                "test_server_ip": "192.168.1.54",
                "test_server_port": 5201,
                "test_server_name": "Local - iperf3 Local",
                "test_server_udp_bandwidth":"10M",
                "test_server_udp_time": "10",
                "test_server_interval": "10",
                "udp_test": {
                    "available": True,
                    "timestamp": "Thu, 28 Dec 2017 16:16:52 GMT",
                    "socket": 4,
                    "start": 0,
                    "end": 10.000331,
                    "seconds": 10.000331,
                    "bytes": 12386304,
                    "bits_per_second": 9908715.059617,
                    "jitter_ms": 0.171,
                    "lost_packets": 2,
                    "packets": 1512,
                    "lost_percent": 0.132275,
                    "out_of_order": 0
                }
            }
        ]
    """
    localsyslog.info("RunUDPTests: UDP measurements..." + str(udp_server))
    
    return udp_servers

"""
Content of iperf3 udp
{
    "start": {
        "connected": [
            {
                "socket": 4,
                "local_host": "192.168.1.4",
                "local_port": 46375,
                "remote_host": "192.168.1.5",
                "remote_port": 5201
            }
        ],
        "version": "iperf 3.1.3",
        "system_info": "Linux nuc-i3 4.13.0-21-generic #24-Ubuntu SMP Mon Dec 18 17:29:16 UTC 2017 x86_64",
        "timestamp": {
            "time": "Thu, 28 Dec 2017 15:40:04 GMT",
            "timesecs": 1514475604
        },
        "connecting_to": {
            "host": "192.168.1.5",
            "port": 5201
        },
        "cookie": "nuc-i3.1514475604.146266.1bbb59d16ae",
        "test_start": {
            "protocol": "UDP",
            "num_streams": 1,
            "blksize": 8192,
            "omit": 0,
            "duration": 10,
            "bytes": 0,
            "blocks": 0,
            "reverse": 0
        }
    },
    "intervals": [
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 0,
                    "end": 10.000331,
                    "seconds": 10.000331,
                    "bytes": 12386304,
                    "bits_per_second": 9908715.295851,
                    "packets": 1512,
                    "omitted": false
                }
            ],
            "sum": {
                "start": 0,
                "end": 10.000331,
                "seconds": 10.000331,
                "bytes": 12386304,
                "bits_per_second": 9908715.295851,
                "packets": 1512,
                "omitted": false
            }
        }
    ],
    "end": {
        "streams": [
            {
                "udp": {
                    "socket": 4,
                    "start": 0,
                    "end": 10.000331,
                    "seconds": 10.000331,
                    "bytes": 12386304,
                    "bits_per_second": 9908715.059617,
                    "jitter_ms": 0.171,
                    "lost_packets": 2,
                    "packets": 1512,
                    "lost_percent": 0.132275,
                    "out_of_order": 0
                }
            }
        ],
        "sum": {
            "start": 0,
            "end": 10.000331,
            "seconds": 10.000331,
            "bytes": 12386304,
            "bits_per_second": 9908715.059617,
            "jitter_ms": 0.171,
            "lost_packets": 2,
            "packets": 1512,
            "lost_percent": 0.132275
        },
        "cpu_utilization_percent": {
            "host_total": 1.229884,
            "host_user": 0.292187,
            "host_system": 0.937697,
            "remote_total": 0.007007,
            "remote_user": 0,
            "remote_system": 0.007007
        }
    }
}
"""



    

def RunTests(sensor_info):
    """
        Will call other functions in order to get all the tests
        - RunIperf3Tests
        - RunDelayTests
        - RunUDPTests
    """
    import time

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)
    localsyslog.info("RunTests: Starting ALL tests with "
        + str(len(sensor_info["wlansensor_info"]["test_servers"]))
        + " test servers...")
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    timestamp_influxdb = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())
    
    iperf3results = RunIperf3Tests(sensor_info)
    #time.sleep(1)
    delayresults = RunDelayTests(sensor_info)
    #time.sleep(1)
    udpresults = RunUDPTests(sensor_info)
    
    # Let's combine all results in one list of dict
    testresults = iperf3results.copy()
    
    for i,testresult in enumerate(testresults):
        testresult.update(delayresults[i].copy())
        testresult.update(udpresults[i].copy())
        testresult["location"] = sensor_info["wlansensor_info"]["location"]
        testresult["name"] = sensor_info["wlansensor_info"]["name"]
        testresult["description"] = sensor_info["wlansensor_info"]["description"]
        testresult["sensor_id"] = sensor_info["wlansensor_info"]["sensor_id"]
        testresult["ssid"] = str(sensor_info["wlansensor_info"]["ssid"])
        testresult["time"] = timestamp
        testresult["time_influxdb"] = timestamp_influxdb
        testresult["dev"] = sensor_info["wlansensor_info"]["dev"]
        testresult["MACaddr"] = sensor_info["wlansensor_info"]["MACaddr"]
        testresult["channel"] = int(sensor_info["wlansensor_info"]["channel"])
        testresult["width"] = int(sensor_info["wlansensor_info"]["width"])
        testresult["Freq"] = int(sensor_info["wlansensor_info"]["Freq"])
        testresult["CenterFreq"] = int(sensor_info["wlansensor_info"]["CenterFreq"])
        testresult["txpower"] = float(sensor_info["wlansensor_info"]["txpower"])
        testresult["Virtual-AP"] = sensor_info["wlansensor_info"]["Virtual-AP"]
        testresult["SSID"] = sensor_info["wlansensor_info"]["SSID"]
        testresult["signal"] = int(sensor_info["wlansensor_info"]["signal"])
        testresult["tx_bitrate"] = float(sensor_info["wlansensor_info"]["tx_bitrate"])
        testresult["MCS"] = int(sensor_info["wlansensor_info"]["MCS"])
        testresult["dtim"] = int(sensor_info["wlansensor_info"]["dtim"])
        testresult["beacon"] = int(sensor_info["wlansensor_info"]["beacon"])
        

    """
    RESULTING LIST of DICT:
    testresults = [
        {
            "test_server_ip": "192.168.1.54",
            "test_server_port": 5201,
            "test_server_name": "Local - iperf3 Local",
            "test_server_udp_bandwidth": "10M",
            "test_server_udp_time": "10",
            "test_server_interval": "10",
            "location":"ALE LAB Test",
            "name":"ALE-Test01",
            "description":"Sonda de pruebas en test",
            "ssid":"AENA",
            "sensor_id":"2",
            "dev":"wlp58s0",
            "MACaddr":"f8:63:3f:28:05:e1",
            "channel":"11",
            "width":"20",
            "Freq":"2462",
            "txpower":"22.00",
            "Virtual-AP":"18:64:72:ea:f0:e4",
            "SSID":"Rivendel",
            "signal":"-17",
            "tx_bitrate":144.4,
            "MCS":"15",
            "dtim":"1",
            "beacon":"100"
            "tcp_test": {
                "available": True,
                "timestamp": "2017-12-28 18:43:17",
                "socket": 4,
                "start": 0,
                "end": 10.000525,
                "seconds": 10.000525,
                "bytes": 444473728,
                "bits_per_second": 355560315.564814,
                "retransmits": 0,
                "max_snd_cwnd": 3075552,
                "max_rtt": 14185,
                "min_rtt": 5595,
                "mean_rtt": 9152
            },
            "udp_test": {
                "available": true,
                "timestamp": "Thu, 28 Dec 2017 16:16:52 GMT",
                "socket": 4,
                "start": 0,
                "end": 10.000331,
                "seconds": 10.000331,
                "bytes": 12386304,
                "bits_per_second": 9908715.059617,
                "jitter_ms": 0.171,
                "lost_packets": 2,
                "packets": 1512,
                "lost_percent": 0.132275,
                "out_of_order": 0
            },
            "delay_test": {
                "available": true,
                "timestamp": "Thu, 28 Dec 2017 16:16:52 GMT",
                "d_packets_sent": "20",
                "d_packets_received": "20",
                "d_packet_loss": "0",
                "d_packet_loss_percent": "0",
                "d_time": "3812",
                "d_rtt_min_ms": "2.804",
                "d_rtt_avg_ms": "42.068",
                "d_rtt_max_ms": "202.262",
                "d_rtt_mdev_ms": "47.512",
                "d_ipg_ms": "200.652",
                "d_ewma_ms": "32.505"
            }
        }
    ]
    """
    return testresults
    

    
    
    
def SendSyslogTestsResults(syslog_handlers, testresult):
    """
        Let's send the test results to the syslog servers...
    """
    import json

    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    for syslog_server in syslog_handlers:
                    
        # Remove overwhelming information for syslog
        
        #print(testresult)
        syslog_data = testresult.copy()
        tcp_test = syslog_data.pop("tcp_test")
        udp_test = syslog_data.pop("udp_test")
        delay_test = syslog_data.pop("delay_test")
        
        # Let's add relevant information to syslog
        if tcp_test["available"]:
            syslog_data["timestamp"] = tcp_test["timestamp"]
            # tcp
            syslog_data["tcp_bits_per_second"] = float(tcp_test["bits_per_second"])
            syslog_data["tcp_retransmits"] = tcp_test["retransmits"]
            syslog_data["tcp_max_rtt"] = tcp_test["max_rtt"]
            syslog_data["tcp_min_rtt"] = tcp_test["min_rtt"]
            syslog_data["tcp_mean_rtt"] = tcp_test["mean_rtt"]
        
        if udp_test["available"]:
            # udp
            syslog_data["udp_jitter_ms"] = float(udp_test["jitter_ms"])
            syslog_data["udp_lost_packets"] = udp_test["lost_packets"]
            syslog_data["udp_lost_percent"] = float(udp_test["lost_percent"])
            syslog_data["udp_out_of_order"] = udp_test["out_of_order"]
        
        if delay_test["available"]:
            # delay
            syslog_data["d_packet_loss"] = delay_test["d_packet_loss"]
            syslog_data["d_packet_loss_percent"] = float(delay_test["d_packet_loss_percent"])
            syslog_data["d_rtt_min_ms"] = float(delay_test["d_rtt_min_ms"])
            syslog_data["d_rtt_avg_ms"] = float(delay_test["d_rtt_avg_ms"])
            syslog_data["d_rtt_max_ms"] = float(delay_test["d_rtt_max_ms"])
            syslog_data["d_rtt_mdev_ms"] = float(delay_test["d_rtt_mdev_ms"])
            syslog_data["d_ipg_ms"] = float(delay_test["d_ipg_ms"])
            syslog_data["d_ewma_ms"] = float(delay_test["d_ewma_ms"])
                   
        # send the information using the syslog handlers
        localsyslog.info("Sending test results to syslog/splunk server: "
            + str(syslog_server))

        syslog_server.info(json.dumps(syslog_data))



def SendInfluxDBTestResults(influxclients, testresult):
    """
        Let's send the Test results to the InfluxDB servers...
    """
    import sys
    import json
    # Attach to LOCAL SYSLOG
    localsyslog = logging.getLogger(logname)

    localsyslog.info("SendInfluxDBTestResults: Sending test results to InfluxcDB clients...")
    
    influxdb_result = testresult.copy()
    
    tcp_test = influxdb_result.pop("tcp_test")
    udp_test = influxdb_result.pop("udp_test")
    delay_test = influxdb_result.pop("delay_test")
    
    for influxdbclient in influxclients:
    
        localsyslog.info("SendInfluxDBTestResults: Connecting with InfluxDB server <"
            + influxdbclient["influxdb_name"]
            + "> with IP/TCP: " + influxdbclient["influxdb_ip"]
            + "/" + str(influxdbclient["influxdb_port"]))
        
        # Check IP ping with InfluxDB Server
        localsyslog.info("SendInfluxDBTestResults: Checking IP connectivity with InfluxDB server: "
            + influxdbclient["influxdb_ip"])
        if not CheckIPConnection(influxdbclient["influxdb_ip"]):
            localsyslog.error("SendInfluxDBTestResults: "
                + influxdbclient["influxdb_ip"] + " not ping reachable... "
                + "Creating the InfluxDB Client handler in any case.")

        influxdb_data = {}
        influxdb_data = [
            {
                "time": tcp_test["timestamp_influxdb"],
                "measurement": "WLAN_Analytics",
                "fields":  {
                    "w_vap":influxdb_result["Virtual-AP"],
                    "w_channel":influxdb_result["channel"],
                    "w_channel_width":influxdb_result["width"],
                    "w_frequency":influxdb_result["Freq"],
                    "w_center_frequency":influxdb_result["CenterFreq"],
                    "w_tx_power":influxdb_result["txpower"],
                    "w_rx_signal":influxdb_result["signal"],
                    "w_tx_bitrate":influxdb_result["tx_bitrate"],
                    "w_mcs":influxdb_result["MCS"],
                    "w_beacon":influxdb_result["beacon"],
                    "w_dtim":influxdb_result["dtim"]
                    
                },
                "tags": {
                    "sensor": influxdb_result["sensor_id"],
                    "name": influxdb_result["name"],
                    "location": influxdb_result["location"],
                    "ssid": influxdb_result["ssid"],
                    "test_server_ip": influxdb_result["test_server_ip"],
                    "test_server_name": influxdb_result["test_server_name"]
                },
            }
        ]
        
        if tcp_test["available"]:
            tcp_influxdb = {}
            tcp_influxdb = {
                "tcp_bytes": tcp_test["bytes"],
                "tcp_seconds": tcp_test["seconds"],
                "tcp_bits_per_second": float(tcp_test["bits_per_second"]),
                "tcp_retransmits": tcp_test["retransmits"],
                "tcp_max_rtt": tcp_test["max_rtt"],
                "tcp_min_rtt": tcp_test["min_rtt"],
                "tcp_mean_rtt": tcp_test["mean_rtt"]
            }
            influxdb_data[0]["fields"].update(tcp_influxdb)
        
        if udp_test["available"]:
            udp_influxdb = {}
            udp_influxdb = {
                "udp_jitter_ms": float(udp_test["jitter_ms"]),
                "udp_lost_packets": udp_test["lost_packets"],
                "udp_lost_percent": float(udp_test["lost_percent"]),
                "udp_out_of_order": udp_test["out_of_order"],
            }
            influxdb_data[0]["fields"].update(udp_influxdb)
        
        if delay_test["available"]:
            delay_influxdb = {}
            delay_influxdb = {
                "d_packet_loss": delay_test["d_packet_loss"],
                "d_packet_loss_percent": delay_test["d_packet_loss_percent"],
                "d_rtt_min_ms": delay_test["d_rtt_min_ms"],
                "d_rtt_avg_ms": delay_test["d_rtt_avg_ms"],
                "d_rtt_max_ms": delay_test["d_rtt_max_ms"],
                "d_rtt_mdev_ms": delay_test["d_rtt_mdev_ms"],
                "d_ipg_ms": delay_test["d_ipg_ms"],
                "d_ewma_ms": delay_test["d_ewma_ms"],
            }
            influxdb_data[0]["fields"].update(delay_influxdb)
        
        
        
        # Write data into InfluxDB
        localsyslog.info("SendInfluxDBTestResults: Sending Tests results to InfluxDB server: "
            + influxdbclient["influxdb_ip"] + " en la base de datos <"
            + influxdbclient["influxdb_db"] + ">")
        localsyslog.info("SendInfluxDBTestResults: writing measurement " 
            + str(influxdb_data))
        
        try:
            influxdbclient["influxdbhandler"].write_points(influxdb_data, protocol='json')
     
        except:
            localsyslog.error("SendInfluxDBTestResults: Failure writing points to DB " 
                + influxdbclient["influxdb_db"]
                + " in InfluxDB server: " 
                + influxdbclient["influxdb_ip"])
            localsyslog.error("SendInfluxDBTestResults: " + str(sys.exc_info()[0]))
            localsyslog.error("SendInfluxDBTestResults: " + str(sys.exc_info()[1]))
            localsyslog.debug("SendInfluxDBTestResults: Error writing points in database <"
                + influxdbclient["influxdb_db"]
                + "> in InfluxDB Server <"
                + influxdbclient["influxdb_ip"]
                + ">. Please check connectivity and status of InfluxDB Server")



def main():
    
    import subprocess
    import json
    import pprint
    import time
    import sys
    from influxdb import InfluxDBClient
    from influxdb.exceptions import InfluxDBClientError
    
    start = time.perf_counter()
    # Initialize the Local syslog for script messages
    localsyslog = LocalSyslogInitialization(logname)
    localsyslog.info("wlansensor initiated...")

    # Recover information from wlansensor.cfg
    localsyslog.info("Reading configuration file "+configuration_file+"...")
    sensor_info = ReadConfigFile(configuration_file)

    #pythonic way would be "if not sensor_info :", but prefer readability:
    if len(sensor_info) == 0:
        # There is no configuration file... have to quit
        localsyslog.critical("No configuration file ("+configuration_file
            + "). Impossible to recover the minimun information to work...")
        localsyslog.critical("Exiting wlansensor application:"
            + " NO CONFIGURATION FILE")
        localsyslog.debug("Please, create "+configuration_file)
        # EXIT the script
        sys.exit("No configuration file available, imposible to get "
            + "information to run. Please create " + configuration_file)

    localsyslog.info("Configuration information successfully loaded from file.")
    localsyslog.info(sensor_info)

    # Update sensor_info >lastconnection< field with the current time
    sensor_info["wlansensor_info"]["lastconnection"] = time.strftime(
                                    "%a, %d %b %Y %H:%M:%S", time.localtime())


    # Check WLAN connectivity
    sensor_info["wlansensor_info"].update(CheckWLANConnection(sensor_info))
    localsyslog.info(sensor_info)
    
    ######################################################################
    # Initialize the UDP syslog servers
    ######################################################################
    syslog_handlers = []
    for i, element in enumerate(sensor_info["wlansensor_info"]["syslog_servers"]):

            localsyslog.info("Initialization of remote syslog >"
                + element["syslog_name"]
                + "> with IP/UDP: "+element["syslog_ip"]
                + "/"
                + str(element["syslog_port"])
            )

            syslog_handlers.append( SyslogInitialization(
                                    sensor_info["wlansensor_info"]["name"],
                                    syslog_server=element["syslog_ip"],
                                    syslog_UDP_port=element["syslog_port"])
            )

    ######################################################################
    # Initialize and Connect to MongoDB servers
    ######################################################################
    localsyslog.info("Initialization and connection with MongoDB servers...")
    mongoclient=[]
    mongodb=[]
    sensors=[] 
    analytics=[]
    for i, element in enumerate(sensor_info["wlansensor_info"]["mongodb_servers"]):
            
            localsyslog.info("Connection with MongoDB server ->"
                + element["mongodb_name"]
                + "<- with IP/TCP: "+element["mongodb_ip"]
                + "/" + str(element["mongodb_port"]))

            mongoclient.append( MongoConnection(
                                    mongo_server=element["mongodb_ip"],
                                    mongo_port=element["mongodb_port"]
                                )
            )

            # Select the database to use in each server, coming from the configuration file
            localsyslog.info("Selecting the Database "
                + element["mongodb_db"] + " in MongoDB server "
                + element["mongodb_name"] + " ("+element["mongodb_ip"]
                + "/" + str(element["mongodb_port"]) + ")")
            mongodb.append( SelectMongoDB(
                                mongoclient[i], 
                                element["mongodb_db"]
                            )
            )

            # Select the Collections for sensors information and analytics
            # Using fixed Collections names:
            # "sensors" for sensors information: id, IP, location, etc.
            # "analytics" for measures of all sensors
            # if needed to be changed, add them to wlansensor.cfg file
            
            """
                analytics = [{
                        "mongodb_ip":"192.168.1.5",
                        "mongodb_port":27017,
                        "mongodb_name":"Local",
                        "mongodb_db":"AENA",
                        "mongodb_available": True,
                        "mongodb_analyticshandler": <object to mongo client pointing to the collection>
                    }
                ]
            """
            
            localsyslog.info("Selecting the Collections 'sensors' and " 
                + "'analytics' in the Database " + element["mongodb_db"]
                + " in MongoDB server " + element["mongodb_name"]
                + " ("+element["mongodb_ip"] + "/" 
                + str(element["mongodb_port"]) + ")")
            
            analytic = element.copy()
            
            if mongodb[i]:
                
                analytic["mongodb_available"] = True
                analytic["mongodb_analyticshandler"] = SelectMongodbCollection(mongodb[i], "analytics")
                
            else:
                # MongoDB Server was down during Connection and Setup stage
                # There are no elements in the <sensors> and <analytics> LISTs
                # No modifications in MongoDB will be done
                analytic["mongodb_available"] = False
                localsyslog.error("MongoDB: MongoDB Server >" 
                    + element["mongodb_name"] + " (" + element["mongodb_ip"]
                    + "/" + str(element["mongodb_port"]) + ") "
                    + "was DOWN during the Connection Establishment Stage, "
                    + "so no ACCESS to Database neither Collections. "
                    + "No updates will be performed in this MongoDB Server.")
            
            sensors.append(SelectMongodbCollection(mongodb[i], "sensors"))
            analytics.append(analytic.copy())
            

    # Update sensor information in MongoDB servers
    Mongodb_sensor_update = []
    for i, element in enumerate(sensors):
        if element:
            Mongodb_sensor_update.append(UpdateMongodbSensorInfo(element, sensor_info))

    
    ######################################################################
    # Initialize and Connect to InfluxDB servers
    ######################################################################
    localsyslog.info("Initialization and connection with InfluxDB servers...")

    influxclients = ConnectInfluxDB(sensor_info)

    # localsyslog.info("Influxclients: " + str(influxclients))
    # localsyslog.info("Influx_client[0]: " + str(influxclients[0]))

    ######################################################################
    # Llamada para obtener los resultados de las pruebas contra
    # los diferentes servidores iperf3
    ######################################################################
    localsyslog.info("Running TESTs with servers...")

    testresults = RunTests(sensor_info)


    ######################################################################
    # Send TEST results
    # to SYSLOG / SPLUNK servers
    # to MongoDB servers
    # to InfluxDB servers 
    ######################################################################
    localsyslog.info("Sending TESTs results to collection servers...")

    MongoDB_insertions = []
    for testresult in testresults:
    
        ####################################################################
        # Send to SYSLOG
        ####################################################################
        SendSyslogTestsResults(syslog_handlers, testresult)

        
        ####################################################################
        # Send to MongoDB
        ####################################################################
        for analytic in analytics:
            MongoDB_insertions.append(WriteMongodbAnalytics(analytic, testresult)) 

            
        ####################################################################
        # Send to InfluxDB
        ####################################################################
        SendInfluxDBTestResults(influxclients, testresult)


    end = time.perf_counter()
    
    localsyslog.info("WLANsensor: Exiting wlansensor, check syslog messages.")
    localsyslog.info("WLANsensor: Execution Time: " + str(end-start) + " seconds.")

if __name__ == "__main__":
    main()

