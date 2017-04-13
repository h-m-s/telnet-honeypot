#!/usr/bin/env python3
import logging
import signal
from engine.server import HoneyTelnetServer
import os
import configparser
import sys

def signal_handler(signal, frame):
    """
    Handles exit on ctrl-c.
    Setting SERVER_RUN ends the main loop below and the server
    will go into clean_exit and close out all open containers.
    """
    print("\nClosing out cleanly...")
    telnet_server.SERVER_RUN = False

def define_logger(settings):
    """
    Sets up the global formatting for logging.

    By default the log file is set to INFO level,
    and DEBUG level will only show up on stdout, but
    another file handler could easily be added.
    """
    FORMAT = '%(asctime)s - %(name)s - %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format=FORMAT)

    try:
        infohandler = logging.FileHandler(settings['log_location'])
    except:
        infohandler = logging.FileHandler("telnet-log.txt")
    infohandler.setLevel(logging.INFO)
    infohandler.setFormatter(logging.Formatter(FORMAT))

    debughandler = logging.StreamHandler()
    debughandler.setLevel(logging.DEBUG)

    logger = logging.getLogger(settings['hostname'])
    logger.addHandler(infohandler)

    """
    Drops the requests loggers to WARNING level.
    Super, duper spammy otherwise, because it'll try to show you
    every GET/POST made to the dockerd
    """
    logging.getLogger("requests").setLevel(logging.WARNING)


def parse_config():
    """
    Parses the local config file for server settings and returns
    a dictionary.
    """
    settings = {}
    config = configparser.ConfigParser()
    config.read('telnet.cfg')
    settings['port'] = config.getint('Telnet', 'port')
    settings['image'] = config.get('Telnet', 'image')
    settings['passwordmode'] = config.getboolean('Telnet', 'password-mode')
    settings['hostname'] = config.get('Telnet', 'hostname')
    settings['log_location'] = config.get('Telnet', 'log')
    settings['address'] = config.get('Telnet', 'address')

    return settings

if __name__ == '__main__':
    """
    Main loop.

    Starts up the loggers, starts up a server, and starts
    the main loop to run until SERVER_RUN is false.
    """
    signal.signal(signal.SIGINT, signal_handler)

    settings = parse_config()

    define_logger(settings)

    telnet_server = HoneyTelnetServer(
        hostname = settings['hostname'],
        port = settings['port'],
        address = settings['address'],
        image = settings['image'],
        passwordmode = settings['passwordmode'],
    )

    logger = logging.getLogger(settings['hostname'])
    logger.info("Listening for connections on port {}. CTRL-C to break.".
                format(telnet_server.port))
    while telnet_server.SERVER_RUN is True:
        telnet_server.poll()
        telnet_server.kick_idle()
        telnet_server.process_clients()

    telnet_server.clean_exit()
