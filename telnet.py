#!/usr/bin/env python3
import logging
import signal
from engine.server import HoneyTelnetServer
import os
import configparser

IDLE_TIMEOUT = 300
SERVER_RUN = True

LOG_LOCATION = "/var/log/hms/telnet-log.txt"

def signal_handler(signal, frame):
    """
    Handles exit on ctrl-c.
    """
    print("\nClosing out cleanly...")
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

def parse_config():
    port = 23
    image = "honeybox"
    passwordmode = False

    config = configparser.ConfigParser()

    try:
        config.read("telnet.cfg")
    except Exception as e:
        print("failed to read")
        print(e)
        return port, image, passwordmode

    try:
        port = config.getint('Telnet', 'port')
        image = config.get('Telnet', 'image')
        passwordmode = config.getboolean('Telnet', 'password-mode')
    except:
        print("failed to parse")
        pass
    return port, image, passwordmode

if __name__ == '__main__':

    """
    Main loop.

    Starts up the loggers, starts up a server, and starts
    the main loop to run until SERVER_RUN is false.
    """
    signal.signal(signal.SIGINT, signal_handler)

    logger = define_logger()

    port, image, passwordmode = parse_config()

    telnet_server = HoneyTelnetServer(
        port=port,
        image=image,
        address='',
        logger=logger,
        passwordmode=passwordmode
        )
    logger.info("Listening for connections on port {}. CTRL-C to break.".
                format(telnet_server.port))
    while telnet_server.SERVER_RUN is True:
        telnet_server.poll()
        telnet_server.kick_idle()
        telnet_server.process_clients()

    telnet_server.clean_exit()
