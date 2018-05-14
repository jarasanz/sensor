#!/usr/bin/env python3

# Modules used along all functions for local syslog
#import logging
#from logging.handlers import SysLogHandler


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
    logname = "WLANsensor"
    
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


    def connectWLAN (self, wlanid=0, ssid=""):
        """
            Try to connect with the wlanid or ssid.
            
            Call the method with:
                self.connectWLAN(wlanid=2)
            or
                self.connectWLAN(ssid="Enterprise-SSID")
                
            <wlanid> takes over <ssid>, so if:
                self.connectWLAN(wlanid=3, ssid="SSID-Demo")
            will use wlanid=3 information to connecto to ssid
                
            Returns a list [status, reason, wirelessinfo]:
                status:
                    True  -> Connection Success
                    False -> Connection Failure
                reason:
                    Message with failure information
                wirelessinfo:
                    Important and needed informationm about the wirelessinfo
                    connection
        """
        from wireless import Wireless
        
        wireless = Wireless(self.logname)
        
        # Let's find the needed information using either wlanid or ssid
        if (wlanid == 0 and ssid==""):
            # empty call self.connectWLAN()... invalid
            return [False, "Empty call to method", wireless.wirelessinfo]
        elif (wlanid == 0 and ssid != ""):
            # receive the information using the ssid
            for wlan in self.sensor["wlans"]:
                if wlan["configuration"]["ssid"] == ssid:
                    connectinfo = wlan["configuration"]
        elif (wlanid != 0):
            # we receive the information using the wlanid
            for wlan in self.sensor["wlans"]:
                if (wlan["wlanid"] == wlanid):
                    connectinfo = wlan["configuration"]
        
        # connectinfo is wlan["configuration"]
#            "configuration":{
#                "ssid":"Temp",
#                "status":"enable",
#                "band":"auto",
#                "vap":"auto",
#                "auth_method":"psk",
#                "psk":"password-psk",
#                "ipconfig":"dhcp",
#                "ipaddress":"",
#                "netmask":"",
#                "gateway":"",
#                "dns1":"",
#                "dns2":""
#            }
        # Call wireless object method with the right information
        wireless.connectWLAN(connectinfo)
        
        return [True, "All ok !!!", wireless.wirelessinfo]
        


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
                
                
                
                
                
        
        
        
    

