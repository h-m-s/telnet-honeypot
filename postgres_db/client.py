#!/usr/bin/python3
"""
Module
"""
import hashlib
import json
import re
import logging

def sanitize_pattern(client):
    client_list = []
    if (len(client.input_list) < 3):
        return None
    client.input_list = client.input_list[2:] # strips username/pass from input
    for line in client.input_list:
        line = re.sub(r"(\/bin\/busybox [A-Z]{5})", "/bin/busybox", line)
        addresses = re.findall(
            r"(\d\d?\d?\.\d\d?\d?\.\d\d?\d?\.\d\d?\d?:?[0-9]*)",
            line)
        if addresses:
            line = re.sub(
                r"(\d\d?\d?\.\d\d?\d?\.\d\d?\d?\.\d\d?\d?:?[0-9]*)",
                "1.1.1.1", line)
        client_list += [line]
    input_string = ';'.join(client_list)
    md5 = hashlib.md5(input_string.encode("utf8")).hexdigest()
    return(input_string, md5)

def process_attack(client):
    logger = logging.getLogger('telnet')
    if client.ip == '127.0.0.1':
        return
    try:
        sanitized_pattern, md5 = sanitize_pattern(client)
    except TypeError:
        """ If sanitize_pattern returns None, there wasn't enough input to form a pattern. """
        return
    logger.info("Attack pattern stored", extra={
                                             'client_ip': client.ip,
                                             'client_port': client.remote_port,
                                             'attack_md5': md5,
                                             'attack_pattern': sanitized_pattern
                                             })
    
