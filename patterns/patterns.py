"""
get user's input, minus the username/password, as a list of commands
read in from a file that contains a json formatted list of commands to
compare against?
"""
import hashlib
import json
import re

def build_list():
    try:
        with open("patterns.json", "r") as list_file:
            list = json.load(list_file)
        return (list)
    except FileNotFoundError:
        return ({})


def dump_list(list):
    with open("patterns.json", "w") as list_file:
        json.dump(list, list_file)

def check_list(client):
    md5 = 0
    master_list = build_list()
    client_list = []
    try:
        client.input_list = client.input_list[2:]
        if client.input_list == []:
            return
    except:
        return
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
        md5 += int(hashlib.md5(line.encode("utf8")).hexdigest(), 16)
    if str(md5) not in master_list.keys():
        print("New attack pattern found.")
        new_pattern = {'input': client_list, 'name': '', 'downloads': addresses, 'attackers': [client.ip] }
        master_list[str(md5)] = new_pattern
        dump_list(master_list)
    else:
        if master_list[str(md5)]['name'] != '':
            print("Attack pattern recognized as {}".format(master_list[str(md5)]['name']))
        else:
            print("Attack pattern recognized.")
        master_list[str(md5)]['attackers'] += [client.ip]
        master_list[str(md5)]['downloads'] += addresses
        dump_list(master_list)
