#!/usr/bin/env python3
import logging
import docker
import uuid
from miniboa import TelnetServer
from os import listdir
from os.path import isfile, join
import os
import io
import binascii
import signal
import sys

IDLE_TIMEOUT = 300
CLIENT_LIST = []
SERVER_RUN = True
SCRIPTED = ["dd", "cd"]
NOT_FOUND = ["nc", "shell"]
BLACK_LIST = ["sh", "chmod"]

def signal_handler(signal, frame):
    print("\nClosing out cleanly...")
    clean_exit()
    sys.exit(0)

def clean_exit():
    for client in CLIENT_LIST:
        if client.container.diff():
            for difference in client.container.diff():
                md5 = client.container.exec_run("md5sum {}".format(difference['Path'])).decode("utf-8")
                md5 = md5.split(' ')[0]
                logger.info("Saving file {} with md5sum {} from {}".format(difference['Path'], md5, client.addrport()))
                with open("./logs/{}{}{}.tar".format(client.uuid, md5, difference['Path'].split('/')[-1]), "bw+") as f:
                    strm, stat = client.container.get_archive(difference['Path'])
                    f.write(strm.data)
        client.container.remove(force=True)
        CLIENT_LIST.remove(client)


def on_connect(client):
    """
    Sample on_connect function.
    Handles new connections.
    """
    logger.info("Opened connection to {}".format(client.addrport()))
    CLIENT_LIST.append(client)
    client.dclient = docker.from_env()
    client.container = client.dclient.containers.run(
        "busybox", "/bin/sh", detach=True, tty=True)
    client.container.env = client.container.exec_run("env").decode("utf-8")
    client.pwd = "/"
    client.username = None
    client.password = None
    client.uuid = uuid.uuid4()
    client.send("login: ")
    #    overwrite_files(client)

def overwrite_files(client):
    mypath = "./overwrite/"
    for root, subdirs, files in os.walk(mypath):
        for file in files:
            filepath = root + "/" + file
            containerpath = (root + "/")[len(mypath) - 1:]
            with open(filepath, "br+") as f:
                data = io.BytesIO(f.read())
            client.container.exec_run("rm ".format(containerpath + "/" + file))
            client.container.put_archive(containerpath, data)

def on_disconnect(client):
    """
    Sample on_disconnect function.
    Handles lost connections.
    """
    logger.info("Lost connection to {}".format(client.addrport()))
    if client.container.diff():
        for difference in client.container.diff():
            md5 = client.container.exec_run("md5sum {}".format(difference['Path'])).decode("utf-8")
            md5 = md5.split(' ')[0]
            with open("./logs/{}{}.tar".format(md5, difference['Path'].split('/')[-1]), "bw+") as f:
                strm, stat = client.container.get_archive(difference['Path'])
                f.write(strm.data)
    client.container.remove(force=True)
    CLIENT_LIST.remove(client)

def cd_command(client, line):
    if len(line.split(' ')) < 2:
        client.pwd = client.container.exec_run("/bin/sh -c 'echo $HOME'").decode("utf-8")[:-1]
        return
    dir = line.split(' ')[1]
    response = client.container.exec_run('/bin/sh -c "cd ' + client.pwd + ';cd ' + dir + ';pwd' '"').decode("utf-8")
    if "can't cd" in response:
        client.send("sh: cd: can't cd to {}\n".format(dir))
    else:
        client.pwd = response[:-1]
        if (len(client.pwd) > 2) and client.pwd[-1] == '/':
            client.pwd = client.pwd[:-1]

def dd_command(client):
    header = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"
    client.send(header)
    client.send("+10 records in\r\n1+0 records out\n")
"""
    with open("dd", "br+") as f:
        client.send(f.read())
"""
def kick_idle():
    """
    Looks for idle clients and disconnects them by setting active to False.
    """
    # Who hasn't been typing?
    for client in CLIENT_LIST:
        if client.idle() > IDLE_TIMEOUT:
            logger.info("Kicking idle client from {}".format(client.addrport()))
            client.active = False

def process_clients():
    """
    Check each client, if client.cmd_ready == True then there is a line of
    input available via client.get_command().
    """
    for client in CLIENT_LIST:
        if client.active and client.cmd_ready:
            run_cmd(client)

def broadcast(msg):
    """
    Send msg to every client.
    """
    for client in CLIENT_LIST:
        client.send(msg)

def login_screen(client, msg):
    if msg != "":
        if not client.username:
            client.username = msg
            client.send("password: ")
        else:
            client.password = msg
            return_prompt(client)
            logger.info("{} logged in as {}-{}".format(client.addrport(), client.username, client.password))

def run_cmd(client):
    """
    Echo whatever client types, evaluate commands.
    """
    msg = client.get_command()
    if not client.username or not client.password:
        login_screen(client, msg)
        return
    if msg == "":
        return_prompt(client)
        return
    logger.info("{}: '{}'".format(client.addrport(), msg))
#   client.send("{}\n".format(msg)) (no echo)
    if '||' in msg:
        logical_operator(client, msg)
        return_prompt(client)
        return
    msg = msg.split(';');
    for message in msg:
        print(message)
        cmd = message.split(' ')[0]
        if 'quit' in message or 'exit' in message:
            client.active = False
        if cmd == "wget":
            client.download = 1
        if cmd == "cd":
            cd_command(client, message)
        elif cmd == "dd":
            dd_command(client)
        elif cmd == "cat" and "mounts" in message:
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + message + '"'
            response = client.container.exec_run(newcmd).decode("utf-8")
            if "No such" not in response:
                with open("./mounts", "r+") as f:
                    response = f.read()
            client.send('\n' + response)
        elif cmd not in NOT_FOUND and cmd not in BLACK_LIST:
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + message + '"'
            response = client.container.exec_run(newcmd)
            response = response.decode("utf-8", "replace")
            if "syntax error" in response:
                continue
            elif "exec failed" not in response:
                client.send(response)
            else:
                not_found(client, cmd)
        elif cmd not in BLACK_LIST:
            not_found(client, cmd)
    return_prompt(client)

def logical_operator(client, msg):
    msg = msg.split('||')
    exit_status = 0;
    last = 0;
    parenth = 0
    for i in range(len(msg)):
        message = msg[i].strip().split(';')
        for j in range(len(message)):
            line = message[j]
            if parenth == 1:
                exit_status = 0
                parenth = 0
            line = line.strip()
            if line[0] == '(':
                line = line[1:]
                parenth = 0
            if line[-1] == ')':
                line = line[:-1]
                parenth = 1
            if (i >= 1) and (i % 2 != 0) and exit_status == 0 and j == 0:
                continue
            if "dd" in line[:2]:
                dd_command(client)
                continue
            if "cd" in line[:2]:
                cd_command(client, line)
                continue
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + line + '"'
            response = client.container.exec_run(newcmd)
            response = response.decode("utf-8", "replace")
            if "can't open" in response:
                exit_status = 1;
            if "exec failed" not in response:
                client.send(response)
            else:
                not_found(client, line.split(' ')[0])
            if 'quit' in line or 'exit' in line:
                client.active = False

def not_found(client, command):
    client.send("sh: {}: command not found\n".format(command))

def return_prompt(client):
    prompt = "root@cam12:~# "
    client.send(prompt)

if __name__ == '__main__':
    # Create a telnet server with a port, address,
    # a function to call with new connections
    # and one to call with lost connections.
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGINT, signal_handler)
    
    telnet_server = TelnetServer(
        port=23,
        address='',
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        timeout = .2
        )

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    infohandler = logging.FileHandler("log")
    infohandler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    infohandler.setFormatter(formatter)

    logger.addHandler(infohandler)
    
    logger.info("Listening for connections on port {}. CTRL-C to break.".format(telnet_server.port))

    # Server Loop
    while SERVER_RUN:
        telnet_server.poll()        # Send, Recv, and look for new connections
        kick_idle()                 # Check for idle clients
        process_clients()           # Check for client input

    logging.info("Server shutdown.")
