#!/usr/bin/env python3

# Modules used along all functions for local syslog
# import logging
# from logging.handlers import SysLogHandler

from wireless import Wireless
from tests import Test
from outputs import Output

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
            dedicated file, rotate logs, etc. KEY FILE, defaults to "WLANsensor"
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
                 config_file=configuration_file,
                 logname=logname,
                 logging_config_file=local_syslog_config_file
                 ):
        """
            Will initialize the sensor, reading the configuration file
            and creating the sensorinfo attributes
        """
        # FIRST always init the logger, as it's used by rest of methods
        self.logger = self.localsysloginitialization(logname, logging_config_file)

        # All information related with the wlan part of the sensor
        # using the external Class Wireless(), that encapsulates the wlan
        # needs for the sensor
        self.wlan = Wireless(self.logname)

        # All information related with the TESTs is managed with the external
        # class Test(), encapsulating all information and methods needed for
        # the tests to run
        self.test = Test(self.logname)

        # Read the sensor configuration
        self.sensor = self.readconfigfile(config_file)

        # Initialize the Main variable to use, a LIST with all the WLAN
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

        # Init the output part of the sensor
        self.output = Output(self)


    @staticmethod
    def localsysloginitialization(logname, logging_config_file):
        """
            Returns a handler for local syslog, used along all class methods
            :param logname:
            :param logging_config_file:
            :return:
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
        LOG_LOCAL0 = 16  # reserved for local use
        LOG_LOCAL1 = 17  # reserved for local use
        LOG_LOCAL2 = 18  # reserved for local use
        LOG_LOCAL3 = 19  # reserved for local use
        LOG_LOCAL4 = 20  # reserved for local use
        LOG_LOCAL5 = 21  # reserved for local use
        LOG_LOCAL6 = 22  # reserved for local use
        LOG_LOCAL7 = 23  # reserved for local use

        localsyslog = logging.handlers.SysLogHandler(address=('localhost', logging.handlers.SYSLOG_UDP_PORT),
                                                     facility=LOG_LOCAL1, socktype=socket.SOCK_DGRAM)

        # Mandamos todo el logging
        localsyslog.setLevel(logging.DEBUG)

        # Formats the Local Syslog message
        formatter = logging.Formatter('%(asctime)s,%(msecs)d - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
                                      datefmt='%d/%m/%Y %H:%M:%S')
        localsyslog.setFormatter(formatter)

        # Bind the syslog handler with the logger
        logger.addHandler(localsyslog)

        # Test
        logger.info('Local syslog Initializated.')

        return logger

    def readconfigfile(self, config_file=configuration_file):
        """ Reads the config file if exists and returns sensor_info
            with all the current information about the sensor
            If the file does not exist, EXIT the script
            
            FUTURE JOB:
                USE logging.config FOR CONFIGURING THE SYSLOG, BASED ON
                dictConfig(), for receiving a JSON Object, that will be stored
                in config_file = configuration_file
        """
        import json
        import sys
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
                logger.critical("No configuration file (" + config_file
                                     + "). Impossible to recover the minimun information to work...")
                logger.critical("Exiting wlansensor application:"
                                     + " NO CONFIGURATION FILE")
                logger.debug("Please, create " + config_file)
                # EXIT the script
                sys.exit("No configuration file available, imposible to get "
                         + "information to run. Please create " + config_file)

        logger.info(config_file + " successfully read.")
        logger.info("wlansensor information restored in sensorconfig")

        # Let's add the result structs, so later are available
        for wlan in sensorconfig["wlans"]:
            results = []
        #     for test in wlan["tests"]:
        #         result = {}
        #         result["test"] = test["test"]
        #         result["testid"] = test["testid"]
        #         results.append(result)
            wlan["results"] = results.copy()

        return sensorconfig

    def runalltests(self):
        """
            Run all tests in all ssids, and store the results
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        # Let's run all tests
        logger.info("Running all tests on all wlans...")
        testresult = {}
        # Iterate over all the WLANs
        for wlan in self.sensor["wlans"]:
            if wlan["configuration"]["status"] == "enable":
                # WLAN is enabled for testing
                # connect to the ssid of this wlan
                status, reason = self.connectWLAN(wlan["wlanid"])
                # Check if connection was right
                if status > 1:
                    # Something went wrong and could not connect with the ssid
                    logger.info("ERROR: Could not connect with the ssid <" + str(wlan["configuration"]["ssid"]) + ">. Skipping this ssid from tests...")
                    break
                # Successfully connected with the SSID
                # Iterate over tests
                for test in wlan["tests"]:
                    # Let's check if the test is enabled
                    if test["status"] == "enable":
                        # Test is enabled and must be run
                        status, testresult = self.test.runtest(wlan["wlanid"], test)

        return testresult

    def runalltestwlan(self, wlanid):
        """
        run all tests for the specified wlanid
        :param wlanid: Identifies the WLAN where all tests will be run
        :return: [status, results]
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        # Let's run all tests
        logger.info("Running all tests on all wlans...")
        # Let's search for the wlanid in the list of WLANs
        for wlan in self.sensor["wlans"]:
            if wlan["wlanid"] == wlanid:
                # Found the right wlanid
                # Let's see if it's enabled
                if wlan["configuration"]["status"] == "enable":
                    # WLAN is enabled for testing
                    # connect to the ssid of this wlan
                    status, reason = self.connectWLAN(wlan["wlanid"])
                    # Check if connection was right
                    if status > 1:
                        # Something went wrong and could not connect with the ssid
                        logger.info("ERROR: Could not connect with the ssid <" + str(wlan["configuration"]["ssid"]) + ">. Skipping this ssid from tests...")
                        return [2, "ERROR: Could not connect with the ssid <" + str(wlan["configuration"]["ssid"]) + ">. Can't run tests..."]
                    # Successfully connected with the SSID
                    # Iterate over tests
                    wlansindex = self.sensor["wlans"].index(wlan)
                    self.sensor["wlans"][wlansindex]["results"] = []
                    results = []
                    for test in wlan["tests"]:
                        # Let's check if the test is enabled
                        if test["status"] == "enable":
                            # Test is enabled and must be run
                            status, testresult = self.test.runtest(test)
                            if status > 1:
                                # Something went wrong running the test
                                logger.info("ERROR: Problem running the test [" + str(testresult) + "]. Skipping this test")
                                testresult = {}
                                testresult["status"] = "wrong"
                                testresult["testid"] = test["testid"]
                                self.sensor["wlans"][wlansindex]["results"].append(testresult)
                                results.append(testresult)
                            else:
                                # SUCCESS with test
                                logger.info("SUCCESS!! test <" + str(test["test"]) + "> completed.")
                                self.sensor["wlans"][wlansindex]["results"].append(testresult)
                                results.append(testresult)
                        else:
                            # Test is disabled
                            logger.info("Test <" + str(test["test"]) + "> is disabled in configuration. Skipping this test...")
                            testresult = {}
                            testresult["status"] = "disabled"
                            testresult["testid"] = test["testid"]
                            self.sensor["wlans"][wlansindex]["results"].append(testresult)
                            results.append(testresult)
                    # Finish to run the tests
                    return [1, results]
                else:
                    # WLAN is disabled...
                    logger.info("ERROR: WLAN with wlanid <" + str(wlanid) + "> is disabled by configuration. Can't run tests on it.")
                    return [3, "ERROR: WLAN with wlanid <" + str(wlanid) + "> is disabled by configuration. Can't run tests on it."]
        # WLAN not found
        logger.info("ERROR: WLAN with wlanid <" + str(wlanid) + "> NOT found in the list of configured WLANs.")
        return [4, "ERROR: WLAN with wlanid <" + str(wlanid) + "> NOT found in the list of configured WLANs."]


    def runsingletest(self, wlanid, testinfo):
        """
        run a single test in the ssid associated with wlanid
        :param wlanid: wlanid with the WLAN network to test
        :param testinfo: Information about the test to run - struct
        :return: [status, results]
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        # Let's run all tests
        logger.info("Running a single test on specific wlan...")
        # Search for the right WLAN according to wlanid
        found = False
        for wlanitem in self.sensor["wlans"]:
            if wlanitem["wlanid"] == wlanid:
                # Found the WLAN indicated by wlanid
                wlan = wlanitem.copy()
                found = True
                break
        if not found:
            # The WLAN is not in sensor information
            return [2, "There is no WLAN associated with wlanid: <" + str(wlanid) + ">. Test not done."]
        # Found... let's continue
        # Find the index or position of WLAN in self.sensor["wlans"]
        wlansindex = self.sensor["wlans"].index(wlan)
        if wlan["configuration"]["status"] == "enable":
            # WLAN is enabled for testing
            # connect to the ssid of this wlan
            status, reason = self.connectWLAN(wlan["wlanid"])
            # Check if connection was right
            if status > 1:
                # Something went wrong and could not connect with the ssid
                logger.info("ERROR: Could not connect with the ssid <" + str(wlan["configuration"]["ssid"]) + ">. Can NOT run the test.")
                logger.debug(str(reason))
                return [3, "ERROR, could NOT connect with the ssid <" + str(wlan["configuration"]["ssid"]) + ">. Can NOT run the test."]
            # Successfully connected with the SSID
            # Iterate over tests searching for testinfo
            for test in wlan["tests"]:
                # Let's search
                if test["testid"] == testinfo["testid"]:
                    # Found!!! Let's check if the test is enabled
                    if test["status"] == "enable":
                        # Test is enabled and must be run
                        # get the testindex
                        status, testresult = self.test.runtest(test)
                        if status > 1:
                            # Something was WRONG with testing
                            return [6, testresult]
                        else:
                            # SUCCESS running the test
                            # update information
                            self.sensor["wlans"][wlansindex]["results"] = []
                            self.sensor["wlans"][wlansindex]["results"].append(testresult)
                            return [1, testresult]
                    else:
                        # Test NOT enabled, skip
                        logger.info("Test specified in <" + str(testinfo) + ">, is NOT enable in configuration. Skipping test.")
                        return [4, "Test specified in <" + str(testinfo) + ">, is NOT enable in configuration. Skipping test."]

            # NOT found... test is not in the list of test for this WLAN
            logger.info("Test specified in <" + str(testinfo) + ">, is NOT in the list of available tests for WLAN <" + str(wlan["configuration"]["ssid"]) + ">. Can NOT run the test.")
            return [5, "Test specified in <" + str(testinfo) + ">, is NOT in the list of available tests for WLAN <" + str(wlan["configuration"]["ssid"]) + ">. Can NOT run the test."]

    def connectWLAN(self, wlanid=-1, ssid=""):
        """
            Try to connect with the wlanid or ssid.
            
            Call the method with:
                self.connectWLAN(wlanid=2)
            or
                self.connectWLAN(ssid="Enterprise-SSID")
                
            <wlanid> takes over <ssid>, so if:
                self.connectWLAN(wlanid=3, ssid="SSID-Demo")
            will use wlanid=3 information to connecto to ssid
                
            Returns [status, reason]:
                status:
                    1 -> Connection Success
                    2 -> Error. Empty call to method
                    3 -> Error. Could NOT connect to SSID
                    
                reason:
                    Message with failure information
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger

        # Let's find the needed information using either wlanid or ssid
        connectinfo = {}
        if wlanid == -1 and ssid == "":
            # empty call self.connectWLAN()... invalid
            logger.info("Empty call to method, no SSID neither wlanid.")
            return [2, "Empty call to method"]

        elif wlanid == -1 and ssid != "":
            # receive the information using the ssid
            for wlan in self.sensor["wlans"]:
                if wlan["configuration"]["ssid"] == ssid:
                    # SSID found !!
                    logger.info("Connecting using the SSID <" + str(ssid) + ">...")
                    connectinfo = wlan["configuration"]
                    break
            if len(connectinfo) == 0:
                # connectinfo={}... so SSID NOT found
                logger.info("Could NOT find the SSID <" + str(ssid) + "in the SENSOR information...")
                return [4, "SSID not present in the SENSOR information..."]
        elif wlanid > -1:
            # we receive the information using the wlanid
            for wlan in self.sensor["wlans"]:
                if wlan["wlanid"] == wlanid:
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
        status, output = self.wlan.connectWLAN(connectinfo)

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


    def showTest(self, ssid="all"):
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
                    if test["status"] == "enable": showtest["tests"].append(test["test"])
                showtests.append(showtest)

            elif ssid == "all":
                showtest["ssid"] = wlan["configuration"]["ssid"]
                for test in wlan["tests"]:
                    if test["status"] == "enable": showtest["tests"].append(test["test"])

                showtests.append(showtest.copy())

        return showtests

    def gettestinfo(self, wlanid, testid=-1, testservername="", testname=""):
        """
        Returns the test DICT with all the information about a test, using the information
        either in testid OR testname
        testid HAS PRECEDENCE over testservername that has PRECEDENCE over testname
        :param testid: testid of the test to recover from the test list, can be empty and defaults to -1
        :param testservername: name of the test server, can be empty and defaults to ""
        :param testname: name of the test, can be empty and defaults to ""
        :return: a DICT with the information of a test
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        # Let's see what is used to identify the test
        if testid!=-1:
            # Call using testid
            for wlan in self.sensor["wlans"]:
                if wlan["wlanid"] == wlanid:
                    # Found the WLAN
                    for test in wlan["tests"]:
                        if test["testid"] == testid:
                            # Found the test
                            return [1, test]
                    # Test not found in the list of configured tests for the WLAN
                    return [2, "Test ID <"+str(testid)+">, NOT found in the list of configured tests for WLAN <" + str(wlanid) + ">"]
            # WLAN not found
            return [3, "WLAN ID <" + str(wlanid) + ">, NOT found in the list of configured WLAN networks"]
        elif testid == -1 and testservername!="":
            # Call using testservername
            for wlan in self.sensor["wlans"]:
                if wlan["wlanid"] == wlanid:
                    # Found the WLAN
                    for test in wlan["tests"]:
                        if test["test_server_name"] == testservername:
                            # Found the test
                            return [1, test]
                    # Test not found in the list of configured tests for the WLAN
                    return [2, "Test Server Name <"+str(testservername)+">, NOT found in the list of configured tests for WLAN <" + str(wlanid) + ">"]
            # WLAN not found
            return [3, "WLAN ID <" + str(wlanid) + ">, NOT found in the list of configured WLAN networks"]
        elif testid==-1 and testservername=="" and testname != "":
            # Call using testname
            for wlan in self.sensor["wlans"]:
                if wlan["wlanid"] == wlanid:
                    # Found the WLAN
                    for test in wlan["tests"]:
                        if test["test"] == testname:
                            # Found the test
                            return [1, test]
                    # Test not found in the list of configured tests for the WLAN
                    return [2, "Test Name <"+str(testname)+">, NOT found in the list of configured tests for WLAN <" + str(wlanid) + ">"]
            # WLAN not found
            return [3, "WLAN ID <" + str(wlanid) + ">, NOT found in the list of configured WLAN networks"]
        else:
            # Empty Call
            logger.info("Empty call... no results can be retrieved.")
            return [2, "Empty call... no results can be retrieved."]

    def getindexwlans(self, wlanid=-1):
        """
        Returns the position of the wlan in the list of WLANs in self.sensor, using wlanid
        :param wlanid: Used to search the index in the list
        :return: the index in the self.sensor["wlans"] LIST
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        logger.info("Getting the index of wlan, using wlanid...")
        if wlanid == -1:
            # Empty call return -1
            logger.info("Empty call to function...")
            return -1
        # Let's search for the idex
        for wlan in self.sensor["wlans"]:
            if wlan["wlanid"] == wlanid:
                # found !!
                index = self.sensor["wlans"].index(wlan)
                logger.info("WLAN with wlanid <" + str(wlanid) + "> found in position <" + str(index) + ">")
                return index
        # Not found
        logger.info("No WLAN in the list has wlanid = " + str(wlanid))
        return -1

    def getindextests(self, wlanid=-1, testid=-1):
        """
        Returns the position of the test in the list of TESTS in self.sensor, using testid
        :param wlanid: need the wlanid in order to search for the right place
        :param testid: Used to search the index in the list
        :return: the index in the self.sensor["wlans"][x]["tests"] LIST
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        logger.info("Getting the index of test, using testid...")
        if wlanid == -1 and testid == -1:
            # Empty call return -1
            logger.info("Empty call to function...")
            return -1
        elif wlanid == -1 or testid == -1:
            # Bad call, need both paramenters
            logger.info("Bad call, need TWO parameters")
            return -1
        # Let's search for the index
        for wlan in self.sensor["wlans"]:
            if wlan["wlanid"] == wlanid:
                # found !!
                wlanindex = self.sensor["wlans"].index(wlan)
                logger.info("WLAN with wlanid <" + str(wlanid) + "> found in position <" + str(wlanindex) + ">")
                # Let's search for the testid
                for test in wlan["tests"]:
                    if test["testid"] == testid:
                        # Found !!
                        testindex = wlan["tests"].index(test)
                        logger.info("TEST with testid <" + str(testid) + "> found in position <" + str(testindex) + ">")
                        return testindex
                # testid not found
                logger.info("No TEST in the list has testid = " + str(testid))
        # wlanid Not found
        logger.info("No WLAN in the list has wlanid = " + str(wlanid))
        return -1

    def pprint(self):
        import json
        return print(json.dumps(self.sensor, indent=2))