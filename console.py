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
SCRIPTED = ["dd", "cd"]
NOT_FOUND = ["nc", "shell"]
BLACK_LIST = ["sh", "chmod", "docker"]

def signal_handler(signal, frame):
    """ handles exit on ctrl+c """
    print("\nClosing out cleanly...")
    telnet_server.clean_exit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    infohandler = logging.FileHandler("log")
    infohandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    infohandler.setFormatter(formatter)
    logger.addHandler(infohandler)
    telnet_server = HoneyTelnetServer(
        port=23,
        address='',
        logger=logger
        )
    logger.info("Listening for connections on port {}. CTRL-C to break.".format(telnet_server.port))
    while telnet_server.SERVER_RUN:
        telnet_server.poll()
        telnet_server.kick_idle()
        telnet_server.process_clients()
