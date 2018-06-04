#!/usr/bin/env python3

# Modules used along all functions for local syslog
#import logging
#from logging.handlers import SysLogHandler

from wireless import Wireless

# Connectivity Failures File
failures_file = "/home/ale/sensor/sensorwatchdog.json"
    

class Sensor:
    """
        This class wraps the SENSOR, you can run tests and send results...
        Calling the init, for instance sensor = Sensor()
        May include many Initialization parameters:
        
        config_file = PATH_TO_FILE, this file contains all relevant information
            about the sensor, kind of probes, where to report, etc.
            IT IS MANDATORY TO EXIST, otherwise sensor will quit.
            Defaults to "/home/ale/sensor/sensorconfig.json"
            
        logname=NAME, with this name, the Sensor will push local syslog
            information, so the system_admin will be able to move to a 
            decicated file, rotate logs, etc. KEY FILE, defaults to "WLANsensor"
            This name is exported to ALL modules.
        
        local_syslog_config_file = PATH_TO_FILE, this file contains information
            for configuring the Local Syslog. 
            It's NOT MANDATORY.
            Defaults to "/home/ale/sensor/local_syslog_config.json"
        
    """
    
    # Used along the program for local syslog
    logname = "sensor"
    
    # Local syslog configuration file
    local_syslog_config_file = "/home/ale/sensor/local_syslog_config.json"
    
    # Configuration file
    configuration_file = "/home/ale/sensor/sensorconfig.json"
    
    def __init__(self, 
                config_file = configuration_file,
                logname = logname,
                logging_config_file = local_syslog_config_file
                ):
        """
            Will initializate the sensor, reading the configuration file
            and creating the sensorinfo attributes
        """
        # FIRST always init the logger, as it's used by rest of methods
        self.logger = self.LocalSyslogInitialization(logname,logging_config_file)
        
        # All information related with the wlan part of the sensor
        # using the external Class Wireless(), that encapsulates the wlan
        # needs for the sensor
        self.wlan = Wireless(self.logname)
        
        # Read the sensor configuration
        self.sensor = self.ReadConfigFile(config_file)
        
        # Initializate the Main variable to use, a LIST with all the WLAN
        # networks to test, with their connection information. Each WLAN OBJECT
        # has two LISTS inside: TESTS, is the list of tests to run (bandwidth,
        # delay, packet loss, dns test, etc.) and OUTPUTS, the list of output
        # methods to use to send the information
        
        # self.sensor = {
        #                   "sensorinfo":{general information about sensor}}
        #                   "wlans":[
        #                       {
        #                           "wlanid":1
        #                           "configuration":{ssid, ip, etc.}
        #                           "tests":[
        #                               {test1},
        #                               {test2},
        #                               ...,
        #                               {testN}
        #                           ],
        #                           "outputs":[
        #                               {output1},
        #                               {output2},
        #                               ...,
        #                               {outputN}
        #                           ],
        #                           "results":[
        #                               {result_test1},
        #                               {result_test2},
        #                               ...,
        #                               {result_testN}
        #                           ]
        #                       },
        #                       {
        #                           "wlanid":2
        #                           "configuration":{ssid, ip, etc.}
        #                           "tests":[
        #                               {test1},
        #                               {test2},
        #                               ...,
        #                               {testN}
        #                           ],
        #                           "outputs":[
        #                               {output1},
        #                               {output2},
        #                               ...,
        #                               {outputN}
        #                           ],
        #                           "results":[
        #                               {result_test1},
        #                               {result_test2},
        #                               ...,
        #                               {result_testN}
        #                           ]
        #                       },
        #                       {
        #                           "wlanid":3
        #                           "configuration":{ssid, ip, etc.}
        #                           "tests":[
        #                               {test1},
        #                               {test2},
        #                               ...,
        #                               {testN}
        #                           ],
        #                           "outputs":[
        #                               {output1},
        #                               {output2},
        #                               ...,
        #                               {outputN}
        #                           ],
        #                           "results":[
        #                               {result_test1},
        #                               {result_test2},
        #                               ...,
        #                               {result_testN}
        #                           ]
        #                       },
        #                   ]
        #               }
        





        
    def LocalSyslogInitialization (self, logname, logging_config_file):
        """
            Returns a handler for local syslog, used along all class methods
        """
    
        import logging
        import socket
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
        
        localsyslog = logging.handlers.SysLogHandler(address=('localhost', logging.handlers.SYSLOG_UDP_PORT), facility=LOG_LOCAL1, socktype=socket.SOCK_DGRAM)

        # Mandamos todo el logging
        localsyslog.setLevel(logging.DEBUG)
    
    
        # Formats the Local Syslog message
        formatter = logging.Formatter('%(asctime)s,%(msecs)d - %(name)s - %(levelname)s - %(funcName)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
        localsyslog.setFormatter(formatter)
    
        # Bind the syslog handler with the logger
        logger.addHandler(localsyslog)
    
        # Test
        logger.info('Local syslog Initializated.')
        
        return logger

    
    def ReadConfigFile (self, config_file = configuration_file):
        """ Reads the config file if exists and returns sensor_info
            with all the current information about the sensor
            If the file does not exist, EXIT the script
            
            FUTURE JOB:
                USE logging.config FOR CONFIGURING THE SYSLOG, BASED ON
                dictConfig(), for pasing a JSON Object, that will be stored
                in config_file = configuration_file
        """
    
        import os.path
        import json
        
        # Attach to LOCAL SYSLOG
        logger = self.logger
        
        try:
            with open(config_file) as json_data:
                sensorconfig = json.load(json_data)
    
        except OSError as error:
            errno, strerror = error.args
            if errno == 2:
                # File does not exists
                logger.info("Could not find " + config_file
                    + " ... setting sensor_info to {}")
                
                # There is no configuration file... have to quit
                localsyslog.critical("No configuration file ("+configuration_file
                    + "). Impossible to recover the minimun information to work...")
                localsyslog.critical("Exiting wlansensor application:"
                    + " NO CONFIGURATION FILE")
                localsyslog.debug("Please, create "+configuration_file)
                # EXIT the script
                sys.exit("No configuration file available, imposible to get "
                    + "information to run. Please create " + configuration_file)
    
        
        logger.info(config_file + " successfully read.")
        logger.info("wlansensor information restored in sensorconfig")
        
        # Let's add the result structs, so later are available
        for wlan in sensorconfig["wlans"]:
            results = []
            for test in wlan["tests"]:
                result={}
                result["test"] = test["test"]
                results.append(result)
            wlan["results"] = results.copy()

        return sensorconfig



    def runAllTest (self):
        """
            Run all tests in all ssids, and store the results
        """
        return


    def connectWLAN (self, wlanid=-1, ssid=""):
        """
            Try to connect with the wlanid or ssid.
            
            Call the method with:
                self.connectWLAN(wlanid=2)
            or
                self.connectWLAN(ssid="Enterprise-SSID")
                
            <wlanid> takes over <ssid>, so if:
                self.connectWLAN(wlanid=3, ssid="SSID-Demo")
            will use wlanid=3 information to connecto to ssid
                
            Returns [status, reason, wirelessinfo]:
                status:
                    1 -> Connection Success
                    2 -> Error. Empty call to method
                    3 -> Error. Could NOT connect to SSID
                    
                reason:
                    Message with failure information
                wirelessinfo:
                    Important and needed informationm about the wirelessinfo
                    connection
        """
        
        # Attach to LOCAL SYSLOG
        logger = self.logger
        
        logger.info("wlanid: <" + str(wlanid) + ">")
        logger.info("ssid: <" + str(ssid) + ">")
        
        # Let's find the needed information using either wlanid or ssid
        connectinfo = {}
        if (wlanid == -1 and ssid==""):
            # empty call self.connectWLAN()... invalid
            logger.info("Empty call to method, no SSID neither wlanid.")
            return [2, "Empty call to method"]
            
        elif (wlanid == -1 and ssid != ""):
            # receive the information using the ssid
            for wlan in self.sensor["wlans"]:
                if wlan["configuration"]["ssid"] == ssid:
                    # SSID found !!
                    logger.info("Connecting using the SSID...")
                    connectinfo = wlan["configuration"]
                    break
            if len(connectinfo) == 0:
                # connectinfo={}... so SSID NOT found
                logger.info("Could NOT find the SSID in the SENSOR information...")
                return [4, "SSID not present in the SENSOR information..."]
        elif (wlanid > -1):
            # we receive the information using the wlanid
            for wlan in self.sensor["wlans"]:
                if (wlan["wlanid"] == wlanid):
                    # wlan ID is ok
                    logger.info("Connecting using the wlanid to select the WLAN connection information...")
                    connectinfo = wlan["configuration"]
                    break
            if len(connectinfo) == 0:
                # connectinfo={}... so wlanid is NO OK
                logger.info("WLAN ID (wlanid) not matching with a valid wlanid in the SENSOR information.")
                return [5, "WLAN ID (wlanid) not matching with a valid wlanid in the SENSOR information."]

        # Call wireless method with the right information to connect to wlan
        logger.info("Calling wlan.connectWLAN for connecting to SSID <" + str(connectinfo["ssid"]) + ">...")
        status,output = self.wlan.connectWLAN(connectinfo)
        
        if status > 1:
            # something went wrong
            logger.warning("ERROR: Could NOT connect to SSID <" + str(connectinfo["ssid"]) + ">.")
            return [3, "ERROR: Could NOT connect to SSID <" + str(connectinfo["ssid"]) + ">."]
        else:
            # SUCCESS!!! Connected to the right SSID
            logger.info("SUCCESS!!! Successfully connected to the SSID <" + str(connectinfo["ssid"]) + ">.")
            # update wlan information
            self.wlan.getAssociationInfo()
            return [1, "SUCCESS!!! Successfully connected to the SSID <" + str(connectinfo["ssid"]) + ">."]




    def runTest (self, wlanid, testid):
        """
            Run a test in wlanid
        """
        return



    def showTest (self, ssid="all"):
        """
            Returns the tests to be done on specific ssid "ssid" or
            all ssids if no ssid is indicated
        """
        showtests = [];
        
        for wlan in self.sensor["wlans"]:
            showtest = {}
            showtest["tests"] = []
            if wlan["configuration"]["ssid"] == ssid:
                showtest["ssid"] = wlan["configuration"]["ssid"]
                for test in wlan["tests"]:
                    showtest["tests"].append(test["test"])
                showtests.append(showtest)
            
            elif ssid == "all":
                showtest["ssid"] = wlan["configuration"]["ssid"]
                for test in wlan["tests"]:
                    showtest["tests"].append(test["test"])
                
                showtests.append(showtest.copy())
        
        return showtests
                
                
                
                
                
        
        
        
    

