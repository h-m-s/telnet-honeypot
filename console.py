#!/usr/bin/env python3
import logging
import docker
import uuid
from miniboa import TelnetServer
from os import listdir
from os.path import isfile, join
import os
import io

IDLE_TIMEOUT = 300
CLIENT_LIST = []
SERVER_RUN = True
NOT_FOUND = ["nc", "shell"]
BLACK_LIST = ["sh"]

def on_connect(client):
    """
    Sample on_connect function.
    Handles new connections.
    """
    logging.info("Opened connection to {}".format(client.addrport()))
    CLIENT_LIST.append(client)
    client.dclient = docker.from_env()
    client.container = client.dclient.containers.run(
        "busybox", "/bin/sh", detach=True, tty=True)
    client.container.env = client.container.exec_run("env").decode("utf-8")
    client.pwd = "/"
    client.uuid = uuid.uuid4()
#    overwrite_files(client)
    return_prompt(client)

def overwrite_files(client):
    mypath = "./overwrite/"
    for root, subdirs, files in os.walk(mypath):
        for file in files:
            filepath = root + "/" + file
            containerpath = (root + "/")[len(mypath) - 1:]
            with open(filepath, "br+") as f:
                data = io.BytesIO(f.read())
            print(containerpath)
            client.container.exec_run("rm ".format(containerpath + "/" + file))
            client.container.put_archive(containerpath, data)

def on_disconnect(client):
    """
    Sample on_disconnect function.
    Handles lost connections.
    """
    logging.info("Lost connection to {}".format(client.addrport()))
    if client.container.diff():
        for difference in client.container.diff():
            with open("./logs/{}{}.tar".format(client.uuid, difference['Path'].split('/')[-1]), "bw+") as f:
                strm, stat = client.container.get_archive(difference['Path'])
                f.write(strm.data)
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

def kick_idle():
    """
    Looks for idle clients and disconnects them by setting active to False.
    """
    # Who hasn't been typing?
    for client in CLIENT_LIST:
        if client.idle() > IDLE_TIMEOUT:
            logging.info("Kicking idle client from {}".format(client.addrport()))
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

def run_cmd(client):
    """
    Echo whatever client types, evaluate commands.
    """
    msg = client.get_command()
    if msg == "":
        return_prompt(client)
        return
    logging.info("{}: '{}'".format(client.addrport(), msg))
#   client.send("{}\n".format(msg)) (no echo)
    if '||' in msg:
        logical_operator(client, msg)
        return_prompt(client)
        return
    msg = msg.split(';');
    for message in msg:
        cmd = message.split(' ')[0]
        if cmd == "cd":
            cd_command(client, message)
        elif cmd == "cat" and "mounts" in message:
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + message + '"'
            response = client.container.exec_run(newcmd).decode("utf-8")
            if "No such" not in response:
                with open("./mounts", "r+") as f:
                    response = f.read()
            client.send(response)
        elif cmd not in NOT_FOUND and cmd not in BLACK_LIST:
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + message + '"'
            print(newcmd)
            response = client.container.exec_run(newcmd)
            response = response.decode("utf-8")
            print(response)
            if "exec failed" not in response:
                client.send(response)
            else:
                not_found(client, cmd)
        elif cmd not in BLACK_LIST:
            not_found(client, cmd)
        if message == 'quit':
            client.active = False
            print(client.container.diff())
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
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + line + '"'
            response = client.container.exec_run(newcmd)
            response = response.decode("ascii", "replace")
            print(response)
            if "can't open" in response:
                exit_status = 1;
            if "exec failed" not in response:
                client.send(response)
            else:
                not_found(client, line.split(' ')[0])

def not_found(client, command):
    client.send("sh: {}: command not found\n".format(command))

def return_prompt(client):
    prompt = "{} # ".format(client.pwd);
    client.send(prompt)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # Create a telnet server with a port, address,
    # a function to call with new connections
    # and one to call with lost connections.

    telnet_server = TelnetServer(
        port=7777,
        address='',
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        timeout = .05
        )

    logging.info("Listening for connections on port {}. CTRL-C to break.".format(telnet_server.port))

    # Server Loop
    while SERVER_RUN:
        telnet_server.poll()        # Send, Recv, and look for new connections
        kick_idle()                 # Check for idle clients
        process_clients()           # Check for client input

    logging.info("Server shutdown.")
