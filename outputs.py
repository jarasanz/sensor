 #!/usr/bin/env python3

import logging
from osshell import OSshell

class Outputerror(Exception):
    """Base class for exceptions in this Class"""
    pass

class Output:
    """
    This class wraps all methods related with the output of the measurements done
    Currently supporting:
    - Syslof: Send to a remote syslog server the measures
    - MongoDB: Send to a remote MongoDB server the measures
    - InfluxDB: Send to a remote InfluxDB server the measures

    Can be extended as needed... (ElasticSearch, SQL, RESTful, etc.)
    """
    def __init__(self, sensor):
        """
        Initialization, basically local syslog
        :param logname: name of the syslog to use
        :param sensorinfo: struct with ALL the information about the sensor, including the outputs to use
        """
        self.logname = sensor.logname + ".Output"
        self.logger = logging.getLogger(self.logname)
        self.logger.info("Logging initialization of Test... Done.")
        # Initialization of the outputs, storing in self.outputs the handlers
        self.outputs = self.initoutputs(sensor)




    def initoutputs(self, sensor):
        """
        Inits the output: Syslog, MongoDB, InfluxDB, RESTful, etc.
        :param sensor: All the information about the SENSOR
        :return: LIST with outputs
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        logger.info("Initializing all outputs, and assign a handler to each output...")
        # Let's iterate over the outputs in each wlan
        outputs = sensor.sensor["sensorinfo"]
        outputs["outputs"] = []
        outputs["wlaninfo"] = sensor.wlan.getAssociationInfo()
        for wlan in sensor.sensor["wlans"]:
            if wlan["configuration"]["status"] == "disable":
                # WLAN disables, so no TESTS, thus no OUTPUTS
                logger.info("WLAN <" + str(wlan["configuration"]["ssid"]) + ">, disables by configuration, skipping output handler creation.")
                continue
            # WLAN enabled
            logger.info("WLAN <" + str(wlan["configuration"]["ssid"]) + "> ACTIVE, creating output handlers...")
            for out in wlan["outputs"]:
                if out["status"] == "enable":
                    # Output enabled, create the handler
                    # Depending on the output let's init differently
                    if out["output"] == "syslog":
                        # Init remote syslog handler
                        try:
                            handler = self.sysloginitialization(out, sensor.sensor["sensorinfo"])
                        except:
                            logger.info("ERROR: Could NOT create the SYSLOG handler for <" + str(out["syslog_name"]) + ">.")
                            continue
                    elif out["output"] == "mongodb":
                        # Init remote MongoDB server handler
                        try:
                            handler = self.mongodbinitialization(out, sensor.sensor["sensorinfo"])
                        except:
                            logger.info("ERROR: Could NOT create the MongoDB handler for <" + str(out["mongodb_name"]) + ">.")
                            continue
                    elif out["output"] == "influxdb":
                        # Init remote InfluxDB server handler
                        try:
                            handler = self.influxdbinitialization(out, sensor.sensor["sensorinfo"])
                        except:
                            logger.info("ERROR: Could NOT create the InfluxDB handler for <" + str(out["influxdb_name"]) + ">.")
                            continue
                    out["handler"] = handler
                    out["wlanid"] = wlan["wlanid"]
                    outputs["outputs"].append(out.copy())
                else:
                    # Output disabled, skip creating the handler
                    logger.info("Output Disabled")
        return outputs


    def checkipcconnectivity(self, ipaddress):
        """ Check IP connectovity with ipaddress
            returns True if connectivity with 'ipaddress' is ok
            returns False if connectivity with 'ipaddress' is impossible
        """
        os = OSshell(self.logname)
        # /bin/ping will retun 0 if there is ICMP echo response
        # will return 1 if there is NO ICMP echo response
        command_shell = ["/bin/ping","-c2 -w1",ipaddress]
        status, result, errors = os.runoscommand(command_shell)
        # in Python 0 is False, but it's OK for ping
        # in Python 1 is True, but it's NOK for ping
        # so let's change the rule...
        return not result.returncode

    def sysloginitialization(self, outputinfo, sensorinfo):
        """
        Initializes the Remote Syslog server
        :param outputinfo: DICT with all the information about the remote syslog
        :param sensorinfo: DICT with information about the sensor
        :return: handler pointing to the object
        """
        # Create the logger for remote SYSLOG, that is the SPLUNK receiver
        handler = logging.getLogger(sensorinfo["name"])
        handler.setLevel(logging.DEBUG)
        # Attach to LOCAL SYSLOG
        logger = self.logger
        logger.info("Initializing SYSLOG server <" + str(outputinfo["syslog_name"]) + ">, and assign a handler...")
        # Let's check the connectivity and inform to local syslog
        logger.info("Ping to syslog server <" + str(outputinfo["syslog_ip"]) + ">...")
        if self.checkipcconnectivity(outputinfo["syslog_ip"]):
            logger.info("Connectivity with syslog remote Receiver <" + str(outputinfo["syslog_ip"]) + "> OK.")
        else:
            logger.info("Connectivity with syslog remote Receiver <" + str(outputinfo["syslog_ip"]) + "> FAILED.")
            logger.info("Continuing, as it's UDP and could be a temporary problem")

        # Creamos el controlador (handler) indicando la IP y el PUERTO
        udp = logging.handlers.SysLogHandler(address=(outputinfo["syslog_ip"], outputinfo["syslog_port"]))
        # Mandamos todo el logging
        udp.setLevel(logging.DEBUG)
        # Formato del mensaje a enviar
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
        udp.setFormatter(formatter)
        # Bind the syslog handler with the logger
        handler.addHandler(udp)
        # logger.info('Antes de return')
        logger.info("Remote syslog server <" + str(outputinfo["syslog_ip"]) + "> Initialization SUCCESS")
        return handler

    def mongodbinitialization(self, output):
        """
        Initializes the Remote MongoDB server
        :param output: DICT with all the information about the remote MongoDB server
        :return: handler pointing to the object
        """
        return True

    def influxdbinitialization(self, output):
        """
        Initializes the Remote Syslog servers
        :param output: DICT with all the information about the remote InfluxDB server
        :return: handler pointing to the object
        """
        return True

    @property
    def pprint(self):
        import json
        return print(json.dumps(self.outputs, indent=2))

    def MongoConnection(self, mongo_server="192.168.1.5", mongo_port=27017):

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

    def SelectMongoDB(self, mongoclient, dbname):

        from pymongo.errors import ConnectionFailure
        import sys

        # Attach to LOCAL SYSLOG
        logger = self.logger

        try:
            # The ismaster command is cheap and does not require auth.
            mongoclient.admin.command('ismaster')
            # Connect with the right DB name in MongoDB server
            mongodb = mongoclient[dbname]
            logger.info("DB " + dbname + " successfully selected in MongoDB server.")
            return mongodb

        except ConnectionFailure:
            logger.error("DB " + dbname + " could NOT be addressed in MongoDB server.")
            logger.error("pymongo: " + str(sys.exc_info()[0]))
            logger.error("pymongo: " + str(sys.exc_info()[1]))
            logger.debug("Check MongoDB server, connectivity, DB name, etc.")
            logger.debug("pymongo: " + str(sys.exc_info()[0]))
            logger.debug("pymongo: " + str(sys.exc_info()[1]))
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
            # print(mongodb.collection_names())
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
            if sensors.count({"wlansensor_info.sensor_id": sensor_id}) >= 1:
                # sensor_id IS IN the Collection, so let's update
                # Update information
                localsyslog.info("SENSOR already defined in the Collection.")
                localsyslog.info("Let's update the timestamp for the last connection")
                result = sensors.update_one(
                    {"wlansensor_info.sensor_id": sensor_id},
                    {"$set":
                         {"wlansensor_info.lastconnection":
                              sensor_info["wlansensor_info"]["lastconnection"]
                          }
                     })
                localsyslog.info("SENSOR information updated in Collection.")

            else:
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
                              + "server <" + analytic["mongodb_name"] + "> (" + analytic[
                                  "mongodb_ip"] + "), Database name <"
                              + analytic["mongodb_db"] + ">, Collection <analytics>.")
            localsyslog.error("WriteMongodbAnalytics: There is no pointer to Collection."
                              + "Most probaly error, MongoDB server is down during Connection stage.")
            localsyslog.error("WriteMongodbAnalytics: skipping MongoDB insertions...")
            return False
