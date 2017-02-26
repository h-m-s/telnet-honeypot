#!/usr/bin/env python3
import logging
import docker
import uuid
from miniboa import TelnetServer
import os
import io
import signal
import sys

IDLE_TIMEOUT = 300
CLIENT_LIST = []
SERVER_RUN = True
SCRIPTED = ["dd", "cd"]
NOT_FOUND = ["nc", "shell"]
BLACK_LIST = ["sh", "chmod", "docker"]

def signal_handler(signal, frame):
    """ handles exit on ctrl+c """
    print("\nClosing out cleanly...")
    clean_exit()

def clean_exit():
    """ cleans up any orphan containers on the way out """
    for client in CLIENT_LIST:
        if client.container.diff() != None:
            for difference in client.container.diff():
                md5 = client.container.exec_run("md5sum {}".format(difference['Path'])).decode("utf-8")
                md5 = md5.split(' ')[0]
                logger.info("Saving file {} with md5sum {} from {}".format(difference['Path'], md5, client.addrport()))
                with open("./logs/{}{}{}.tar".format(client.uuid, md5, difference['Path'].split('/')[-1]), "bw+") as f:
                    strm, stat = client.container.get_archive(difference['Path'])
                    f.write(strm.data)
        print("Closing container...")
        client.container.remove(force=True)
        CLIENT_LIST.remove(client)
    sys.exit(0)

def on_connect(client):
    """
    for new connections, creates a docker container and assigns it to the client 
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
    client.download = 0
    client.uuid = uuid.uuid4()
    client.send("login: ")

def on_disconnect(client):
    """
    for disconnections
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
    """
    hackish CD command
    """
    if len(line.split(' ')) < 2:
        client.pwd = client.container.exec_run("/bin/sh -c 'echo $HOME'").decode("utf-8")[:-1]
        return
    dir = line.split(' ')[1]
    response = client.container.exec_run('/bin/sh -c "cd ' + client.pwd + ';cd ' + dir + ';pwd' '"').decode("utf-8")
    if "can't cd" in response:
        client.send("sh: cd: can't cd to {}\n".format(dir))
        logger.info("sh: cd: can't cd to {}\n".format(dir))
    else:
        client.pwd = response[:-1]
        if (len(client.pwd) > 2) and client.pwd[-1] == '/':
            client.pwd = client.pwd[:-1]

def dd_command(client):
    """
    hackish dd command, need more headers!
    """
    header = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"
    client.send(header)
    client.send("+10 records in\r\n1+0 records out\n")
    logger.info(header)
    logger.info("+10 records in\r\n1+0 records out\n")

def kick_idle():
    """
    kicks idle client
    """
    for client in CLIENT_LIST:
        if client.download == 1:
            client.download = 0
        elif client.idle() > IDLE_TIMEOUT:
            logger.info("Kicking idle client from {}".format(client.addrport()))
            client.active = False

def process_clients():
    """
    if client has a cmd ready, let's run it
    """
    for client in CLIENT_LIST:
        if client.active and client.cmd_ready:
            run_cmd(client)

def login_screen(client, msg):
    """
    if we haven't got a user and a pass yet, force them to the login screen
    currently logs the user/pass but doesn't have any way of filtering them
    """
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
    evaluate commands!
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
        cmd = message.split(' ')[0]
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
            logger.info('\n' + response)
        elif cmd not in NOT_FOUND and cmd not in BLACK_LIST:
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + message + '"'
            response = client.container.exec_run(newcmd)
            response = response.decode("utf-8", "replace")
            if "quit" in cmd or "exit" in cmd:
                client.active = False
            if cmd == "wget":
                client.download = 1
            if "syntax error" in response:
                continue
            elif "exec failed" not in response:
                logger.info(response)
                client.send(response)
            else:
                not_found(client, cmd)
        elif cmd not in BLACK_LIST:
            not_found(client, cmd)
    return_prompt(client)

def logical_operator(client, msg):
    """
    deals with logical operators. need to combine this and the run_cmd into
    a wrapper parsing function that deals with all strings, regardless
    """
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
            if "wget" in line[:4]:
                client.download = 1
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + line + '"'
            response = client.container.exec_run(newcmd)
            response = response.decode("utf-8", "replace")
            if "can't open" in response:
                exit_status = 1;
            if "exec failed" not in response:
                client.send(response)
                logger.info(response)
            else:
                not_found(client, line.split(' ')[0])

def not_found(client, command):
    """
    not found
    """
    client.send("sh: {}: command not found\n".format(command))

def return_prompt(client):
    """
    returns that prompt
    """
    prompt = "root@HMS:~# "
    client.send(prompt)

if __name__ == '__main__':
    """ setup! """
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGINT, signal_handler)
    
    telnet_server = TelnetServer(
        port=23,
        address='',
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        timeout = .02
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
