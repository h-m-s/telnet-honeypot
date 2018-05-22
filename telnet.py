#!/usr/bin/env python3
from telnetlogging import setup_logging
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
    settings['postgres'] = config.getboolean('Telnet', 'postgres')

    return settings

if __name__ == '__main__':
    """
    Main loop.

    Starts up the loggers, starts up a server, and starts
    the main loop to run until SERVER_RUN is false.
    """
    signal.signal(signal.SIGINT, signal_handler)

    settings = parse_config()

    setup_logging()

    telnet_server = HoneyTelnetServer(
        hostname = settings['hostname'],
        port = settings['port'],
        address = settings['address'],
        image = settings['image'],
        passwordmode = settings['passwordmode'],
    )

    logger = logging.getLogger(settings['hostname'])
    telnet_server.postgres = settings['postgres']
    logger.info("[SERVER] Listening for connections on port {}. CTRL-C to break.".
                format(telnet_server.port))
    while telnet_server.SERVER_RUN is True:
        telnet_server.poll()
        telnet_server.kick_idle()
        telnet_server.process_clients()

    telnet_server.clean_exit()
