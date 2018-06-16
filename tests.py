 #!/usr/bin/env python3

import logging
from osshell import OSshell

class Test:

    """
        This class wraps all the TESTS to be done with each WLAN network.
        Will define objects to store the needed information to run each kind
        of test (Bandwidth, Delay, Packet loss, etc.)
        RESULTS are stored in the same object, so can be later reviewed and sent
        to the outputs
        Will be in-charge of running the tests.
    """
    
    def __init__(self, logname="log"):
        """
            Initializate the Test Class
        """
        # Initialize the logging
        self.logname = logname + ".Test"
        self.logger = logging.getLogger(self.logname)
        self.logger.info("Logging initialization of Test... Done.")
        self.results = {}

    def runtest(self, testinfo):
        """
            Run a test in wlanid with the information from testinfo
            testinfo could be any of the following forms... and future (dns performance, dhcp performance, etc.)
            {
                "test":"bandwidth",
                "testid":1,
                "status":"enable",
                "test_server_ip":"192.168.1.5",
                "test_server_port":"5201",
                "test_server_name":"Local - iperf3 Local"
            }
            {
                "test":"delay",
                "testid":2,
                "status":"enable",
                "test_server_ip":"192.168.1.5",
                "test_server_name":"Delay Test Server",
                "test_server_delay_packets_to_send":"50"
            }
            {
                "test":"packetLoss",
                "testid":3,
                "status":"enable",
                "test_server_ip":"192.168.1.5",
                "test_server_port":"5201",
                "test_server_name":"Packet-loss Server",
                "test_server_udp_bandwidth":"10M",
                "test_server_udp_time": "10",
                "test_server_udp_interval": "10"
            }
            {
                "test":"dns",
                "testid":4,
                "status":"enable",
                "dns_server_ip":"8.8.8.8",
                "dns_server_name":"google DNS1"
            }
        """
        # Attach to LOCAL SYSLOG
        logger = self.logger
        # Let's run a test
        logger.info("Running a single test and return results...")

        # Let's call the right method, depending on the test
        if testinfo["test"] == "bandwidth":
            # Bandwidth test
            logger.info("Call to run a <" + str(testinfo["test"]) + "> test...")
            status,self.results = self.runbandwidthtest(testinfo)
        elif testinfo["test"] == "delay":
            # Delay test
            logger.info("Call to run a <" + str(testinfo["test"]) + "> test...")
            status,self.results = self.rundelaytest(testinfo)
        elif testinfo["test"] == "packetloss":
            # Packet Loss test
            logger.info("Call to run a <" + str(testinfo["test"]) + "> test...")
            status,self.results = self.runudptest(testinfo)
        else:
            # Non supported test
            logger.info("ERROR: <" + str(testinfo["test"]) + "> test is not supported yet...")
            return [2, testinfo["test"]+" test is not supported yet..."]

        # Let's check the return status and return
        if status > 1:
            # Something was WRONG with the test
            logger.info("ERROR: something was wrong running the test...")
            logger.info("ERROR: " + str(self.results))
            return [3, self.results]
        else:
            # SUCCESS !!!!
            logger.info("SUCCESS!!! Test done successfully.")
            return [1, self.results]

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

    def runbandwidthtest(self, testinfo):
        """
            Let's run the iperf3 Bandwidth tests with the info in testinfo
            {
                "test":"bandwidth",
                "testid":1
                "status":"enable",
                "test_server_ip":"192.168.1.5",
                "test_server_port":"5201",
                "test_server_name":"Local - iperf3 Local"
            }
            return [status, result]
                status:
                1 -> OK
                2 -> Test server NOT IP reachable
                3 -> Iperf3 service not ready in the server when running the test
                result:
                {
                    "timestamp": "2017-12-28 18:43:17",
                    "testid": 1,
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
        """
        import time
        import json

        # Attach to LOCAL SYSLOG
        logger = self.logger
        logger.info("Starting BANDWIDTH test with <" +str(testinfo["test_server_name"]) + "> server [" + str(testinfo["test_server_ip"]) + ":" + str(testinfo["test_server_port"]) + "]")
        # Instantiate an OSshell for calling the OS
        os = OSshell(self.logname)
        # Let's PING the TEST SERVERS, for ARP and DNS resolution and cache
        logger.info("Will now ping test server for caching MAC and DNS... (avoiding false results)")
        if not self.checkipcconnectivity(testinfo["test_server_ip"]):
            # Server NOT reachable... skip this test
            logger.error("ERROR: Test Server: <" + str(testinfo["test_server_ip"]) + "> is NOT IP reachable... Will skip this TCP Bandwidth Test.")
            return [2, "Test Server not IP reachable..."]
        else:
            # Ping success, now it must be in ARP table
            logger.info("Test Server: <" + str(testinfo["test_server_ip"]) + "> is now in ARP/DNS cache.")
            logger.info("Running the TCP Bandwidth test...")
            # Call iperf3
            command_shell = ["/usr/bin/iperf3", "--client", testinfo["test_server_ip"]]
            command_shell += ["--port", testinfo["test_server_port"], "--json"]
            status, result, errors = os.runoscommand(command_shell)
            # Get timestamp when test finished
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # Check test result
            if result.returncode:
                # Server down, unreachable
                logger.error("ERROR: TCP Test FAILURE with Test Server <" + testinfo["test_server_ip"] + ">. Not reachable for testing...")
                logger.debug("ERROR: " + result.stdout.decode("utf-8"))
                logger.debug("ERROR: " + str(errors))
                return [3, "Iperf3 service was NOT ready in Server when running the test..."]
            else:
                # TCP Test SUCCESS !!!!
                logger.info("SUCCESS!!! TCP Test with server <" + testinfo["test_server_ip"] + "> successfully done.")
                # Adapt the output, so only contains relevant information
                # and add Timestamp
                j1 = json.loads(result.stdout.decode("utf-8"))
                output = j1["end"]["streams"][0]["sender"]
                output["timestamp"] = timestamp
                output["testid"] = testinfo["testid"]
                output["status"] = "ok"
                """
                    output = {
                                "timestamp": "2017-12-28 18:43:17",
                                "testid":1,
                                "status": "ok",
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
                """
                logger.info("TCP measurements: <" + str(output) + ">")
                return [1, output]
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

    def rundelaytest(self, testinfo):
        """
            Let's run the delay test with the information in testinfo
            Using ping for round-trip time delay
            {
                "test":"delay",
                "testid":2,
                "status":"enable",
                "test_server_ip":"192.168.1.5",
                "test_server_name":"Delay Test Server",
                "test_server_delay_packets_to_send":"50"
            }
        """
        import time
        import json

        # Attach to LOCAL SYSLOG
        logger = self.logger
        logger.info("Starting DELAY test with <" +str(testinfo["test_server_name"]) + "> server [" + str(testinfo["test_server_ip"]) + "]")
        # Instantiate an OSshell for calling the OS
        os = OSshell(self.logname)

        # Let's PING the TEST SERVERS, for ARP and DNS resolution and cache
        logger.info("Will now ping test server for caching MAC and DNS... (avoiding false results)")
        if not self.checkipcconnectivity(testinfo["test_server_ip"]):
            # Server NOT reachable... skip this test
            logger.error("ERROR: Test Server: <" + str(testinfo["test_server_ip"]) + "> is NOT IP reachable... Will skip this DELAY Test.")
            return [2, "Test Server not IP reachable..."]
        else:
            # Ping success, now it must be in ARP table
            logger.info("Test Server: <" + str(testinfo["test_server_ip"]) + "> is now in ARP/DNS cache.")
            logger.info("Running the DELAY test...")
            """
            # Now let's run the delay test...
            # using regular ping tool
            # For better accuracy, a NTP timestamped TCP flow, avoiding IP fragmentation, is preferred... 
            # but for now let's use ping
            # ping -A -q -c 20 <IPADDRESS>
                # -A        -> wait for echo response and send new packet, instead of default 1 second between packets
                # -q        -> run in quiet mode, reporting the statistics at the end
                # -c 20    -> send 20 echo request
            # Adding the results to the output:
            """
            command_shell = ["/bin/ping", "-A", "-q", "-c", testinfo["test_server_delay_packets_to_send"], testinfo["test_server_ip"]]
            status, result, errors = os.runoscommand(command_shell)
            # Get timestamp when test finished
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # Check test result
            if result.returncode:
                # Server down, unreachable
                logger.error("ERROR: DELAY Test FAILURE with Test Server <" + testinfo["test_server_ip"] + ">. Not reachable for testing...")
                logger.debug("ERROR: " + result.stdout.decode("utf-8"))
                logger.debug("ERROR: " + str(errors))
                return [3, "DELAY server was NOT ready when running the test..."]
            else:
                # Delay test SUCCESS !!
                logger.info("SUCCESS!!! DELAY Test with server <" + testinfo["test_server_ip"] + "> successfully done.")
                # Adapt the output, so only contains relevant information
                # and add Timestamp
                """
                    Content of ping output  - p1.stdout.decode("utf-8")
                    [0]PING 192.168.1.54 (192.168.1.54) 56(84) bytes of data.
                    [1]
                    [2]--- 192.168.1.54 ping statistics ---
                    [3]20 packets transmitted, 20 received, 0% packet loss, time 3812ms
                    [4]rtt min/avg/max/mdev = 2.804/42.068/202.262/47.512 ms, pipe 2, ipg/ewma 200.652/32.505 ms
                """
                output={}
                p2 = result.stdout.decode("utf-8").splitlines()
                output["timestamp"] = timestamp
                output["testid"] = testinfo["testid"]
                output["status"] = "ok"
                output["d_packets_sent"] = p2[3].split()[0]
                output["d_packets_received"] = p2[3].split()[3]
                output["d_packet_loss"] = str(int(p2[3].split()[0]) - int(p2[3].split()[3]))
                output["d_packet_loss_percent"] = float(p2[3].split()[5].strip("%"))
                output["d_time"] = p2[3].split()[9].strip("ms")
                output["d_rtt_min_ms"] = float(p2[4].split()[3].split("/")[0])
                output["d_rtt_avg_ms"] = float(p2[4].split()[3].split("/")[1])
                output["d_rtt_max_ms"] = float(p2[4].split()[3].split("/")[2])
                output["d_rtt_mdev_ms"] = float(p2[4].split()[3].split("/")[3])
                output["d_ipg_ms"] = float(p2[4].split()[len(p2[4].split()) - 2].split("/")[0])
                output["d_ewma_ms"] = float(p2[4].split()[len(p2[4].split()) - 2].split("/")[1])

                """
                output = {
                            "timestamp": "Thu, 28 Dec 2017 16:16:52 GMT",
                            "testid":2,
                            "status": "ok",
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
                """
                logger.info("Delay measurements: <" + str(output) + ">")
                return [1, output]

    def runudptest(self, testinfo):
        """
            Let's run the UDP tests with the servers from testinfo
            Using iperf3 for jitter and packet loss
            {
                "test":"packetLoss",
                "testid":3,
                "status":"enable",
                "test_server_ip":"192.168.1.5",
                "test_server_port":"5201",
                "test_server_name":"Packet-loss Server",
                "test_server_udp_bandwidth":"10M",
                "test_server_udp_time": "10",
                "test_server_udp_interval": "10"
            }
        """
        import time
        import json

        # Attach to LOCAL SYSLOG
        logger = self.logger
        logger.info("Starting Packet Loss and Jitter test with <" +str(testinfo["test_server_name"]) + "> server [" + str(testinfo["test_server_ip"]) + ":" + str(testinfo["test_server_port"]) + "]")
        # Instantiate an OSshell for calling the OS
        os = OSshell(self.logname)
        # Let's PING the TEST SERVERS, for ARP and DNS resolution and cache
        logger.info("Will now ping test server for caching MAC and DNS... (avoiding false results)")
        if not self.checkipcconnectivity(testinfo["test_server_ip"]):
            # Server NOT reachable... skip this test
            logger.error("ERROR: Test Server: <" + str(testinfo["test_server_ip"]) + "> is NOT IP reachable... Will skip this Packet Loss and Jitter Test.")
            return [2, "Test Server not IP reachable..."]
        else:
            # Ping success, now it must be in ARP table
            logger.info("Test Server: <" + str(testinfo["test_server_ip"]) + "> is now in ARP/DNS cache.")
            logger.info("Running the Packet Loss and Jitter test...")
            # Call iperf3
            command_shell = ["/usr/bin/iperf3",
                             "--client", testinfo["test_server_ip"],
                             "--udp",
                             "--interval", testinfo["test_server_udp_interval"],
                             "--time", testinfo["test_server_udp_time"],
                             "--bandwidth", testinfo["test_server_udp_bandwidth"],
                             "--json"
                             ]
            status, result, errors = os.runoscommand(command_shell)
            # Get timestamp when test finished
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # Check test result
            if result.returncode:
                # Server down, unreachable
                logger.error("ERROR: UDP (Packet Loss and Jitter) Test FAILURE with Test Server <" + testinfo["test_server_ip"] + ">. Not reachable for testing...")
                logger.debug("ERROR: " + result.stdout.decode("utf-8"))
                logger.debug("ERROR: " + str(errors))
                return [3, "Iperf3 service was NOT ready in Server when running the test..."]
            else:
                # UDP Test SUCCESS !!!!
                logger.info("SUCCESS!!! UDP Test with server <" + testinfo["test_server_ip"] + "> successfully done.")
                # Adapt the output, so only contains relevant information
                # and add Timestamp
                output = {}
                j1 = json.loads(result.stdout.decode("utf-8"))
                output = j1["end"]["streams"][0]["udp"]
                output["timestamp"] = timestamp
                output["testid"] = testinfo["testid"]
                output["status"] = "ok"
                """
                output =    {
                            "timestamp": "Thu, 28 Dec 2017 16:16:52 GMT",
                            "testid":3,
                            "status": "ok"
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
                """
                logger.info("UDP (Packet Loss and Jitter) measurements: <" + str(output) + ">")
                return [1, output]

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

    def pprint(self):
        import json
        return print(json.dumps(self.results, indent=2))

