#!/usr/bin/env python3
import logging
import signal
from engine.server import HoneyTelnetServer
import os

IDLE_TIMEOUT = 300
SERVER_RUN = True

LOG_LOCATION = "/var/log/hms/telnet-log.txt"

def signal_handler(signal, frame):
    """
    Handles exit on ctrl-c.
    """
    print("\nClosing out cleanly...")
    telnet_server.clean_exit()
    telnet_server.SERVER_RUN = False

def define_logger():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    try:
        infohandler = logging.FileHandler(LOG_LOCATION)
    except:
        infohandler = logging.FileHandler("telnet-log.txt")
    infohandler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    infohandler.setFormatter(formatter)
    logger.addHandler(infohandler)
    return (logger)

if __name__ == '__main__':

    """
    Main loop.

    Starts up the loggers, starts up a server, and starts
    the main loop to run until SERVER_RUN is false.
    """
    signal.signal(signal.SIGINT, signal_handler)

    logger = define_logger()
    telnet_server = HoneyTelnetServer(
        port=23,
        address='',
        logger=logger
        )
    logger.info("Listening for connections on port {}. CTRL-C to break.".
                format(telnet_server.port))
    while telnet_server.SERVER_RUN is True:
        telnet_server.poll()
        telnet_server.kick_idle()
        telnet_server.process_clients()
