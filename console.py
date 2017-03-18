#!/usr/bin/env python3
import logging
import docker
import uuid
from miniboa import TelnetServer
import os
import io
import signal
import sys
import time
from engine.client import HoneyTelnetClient
from engine.server import HoneyTelnetServer

IDLE_TIMEOUT = 300
SERVER_RUN = True

def signal_handler(signal, frame):
    """
    Handles exit on ctrl-c.

    TO DO: double check clean_exit is complete
    """
    print("\nClosing out cleanly...")
    SERVER_RUN = False
    telnet_server.clean_exit()

if __name__ == '__main__':

    """
    Main loop.

    Starts up the loggers, starts up a server, and starts
    the main loop to run until SERVER_RUN is false.
    """
    signal.signal(signal.SIGINT, signal_handler)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    infohandler = logging.FileHandler("log")
    infohandler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    infohandler.setFormatter(formatter)
    logger.addHandler(infohandler)
    telnet_server = HoneyTelnetServer(
        port=23,
        address='',
        logger=logger
        )
    logger.info("Listening for connections on port {}. CTRL-C to break.".
                format(telnet_server.port))
    while SERVER_RUN:
        telnet_server.poll()
        telnet_server.kick_idle()
        telnet_server.process_clients()
