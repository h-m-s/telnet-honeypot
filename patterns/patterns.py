"""
get user's input, minus the username/password, as a list of commands
read in from a file that contains a json formatted list of commands to
compare against?
"""
import hashlib
import json
import re

def build_list(filename="patterns.json"):
    """
    Reads from the patterns.json file to build a list
    of known patterns.
    """
    try:
        with open(filename, "r") as list_file:
            pattern_list = json.load(list_file)
        return (pattern_list)
    except FileNotFoundError:
        return ({})


def dump_list(pattern_list, filename="patterns.json"):
    """
    Turns the dict into a JSON object and dumps it to a given
    file.
    """
    with open(filename, "w") as list_file:
        json.dump(pattern_list, list_file)

def check_list(client, server, filename="patterns.json"):
    """
    Adds up the md5 of  each line of the client's input,
    after parsing it for IPs and certain other things
    (aka, random /bin/busybox applets).
    Then uses that information to decide if it's seen
    the pattern before, and logs the appropriate message.
    If it hasn't, it makes a new entry into the pattern list,
    and if it has, it adds the information to the existing
    key.
    """
    md5 = 0
    master_list = build_list(filename)
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
        server.logger.info("[{}]: NEW ATTACK PATTERN FOUND".format(client.addrport()))
        new_pattern = {'input': client_list,
                       'name': '',
                       'downloads': addresses,
                       'attackers': [client.ip] }
        master_list[str(md5)] = new_pattern
        dump_list(master_list, filename)
    else:
        if master_list[str(md5)]['name'] != '':
            server.logger.info(
                "[{}]: ATTACK PATTERN RECOGNIZED: {}".format(
                    client.addrport(), master_list[str(md5)]['name']))
        else:
            server.logger.info(
                "[{}]: ATTACK PATTERN RECOGNIZED: unnamed".format(client.addrport()))
        master_list[str(md5)]['attackers'] += [client.ip]
        master_list[str(md5)]['downloads'] += addresses
        dump_list(master_list, filename)
