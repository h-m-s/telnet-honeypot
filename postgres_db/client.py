#!/usr/bin/python3
"""
Module
"""
import hashlib
import json
from models import *
from models import storage
import os
import re
import datetime

def add_attacker(attacker_ip):
    query = storage.session.query(Attacker).filter_by(ip=attacker_ip).all()
    if query:
        a = query[0]
        a.count += 1
    else:
        a = Attacker(attacker_ip)
    a.save()
    return(a)

def add_pattern(pattern, md5):
    query = storage.session.query(Pattern).filter_by(pattern_md5=md5).all()
    if query:
        print("MD5 recognized.")
        pattern = query[0]
        pattern.count += 1
    else:
        print("MD5 not recognized.")
        pattern = Pattern(pattern, md5)
    pattern.save()
    return(pattern)

def add_attack(attacker_ip, pattern, md5):
    timestamp = datetime.datetime.utcnow() # add option to change format in config
    host = os.getenv('HOSTNAME', 'honey') # add option to overwrite this in config
    attacker = add_attacker(attacker_ip)
    attack_pattern = add_pattern(pattern, md5)
    attack = Attack(attacker, attack_pattern.pattern_id, host, timestamp)
    attack.save()

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
    input_string = ";".join(client_list)
    md5 = hashlib.md5(input_string.encode("utf8")).hexdigest()
    return(input_string, md5)

def process_attack(client):
    if client.ip == '127.0.0.1':
        return
    try:
        sanitized_pattern, md5 = sanitize_pattern(client)
        add_attack(client.ip, sanitized_pattern, md5)
    except TypeError:
        return
