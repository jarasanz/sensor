#!/usr/bin/env python3

import logging

class OSshell:
    """
        This Class envelopes the object and methods for calling the OS
        with a command shell, this Class execute the command
        and returns
    """
    def __init__(self, logname="log"):
        """
            Initialize
        """
        # Initialize the logging
        self.logname = logname+".OSshell"
        self.logger = logging.getLogger(self.logname)
        self.logger.info("Logging initialization of OSshell. Done.")

    def runoscommand(self, command_shell):
        """
            Run the OS command in <command_shell>, a LIST containing the
            command to run for subprocess
            Return [status,
                    output,
                    [[msg],[errno],[strerror]]
                   ]
                status:
                    1  -> OK, command successfully executed
                    20 -> NOK, problem calling the operating system
        """
        import subprocess
        import sys
        # Attach to LOCAL SYSLOG
        logger = self.logger
        errno = 0
        strerror = ""

        try:
            p1 = subprocess.run(command_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        except OSError as error:
            errno, strerror = error.args
            logger.critical("Couldn't execute command <" + command_shell + ">")
            logger.critical("Error number: " + str(errno))
            logger.critical("Error msg: " + strerror)
            return [20, p1, ["Couldn't execute command <" + str(command_shell) + ">", errno, strerror]]

        return [1, p1, ["Command successfully executed", errno, strerror]]
