#!/usr/bin/env python3
import logging
import docker
from miniboa import TelnetServer

IDLE_TIMEOUT = 300
CLIENT_LIST = []
SERVER_RUN = True
BLACK_LIST = ["nc"]

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
    return_prompt(client)

def on_disconnect(client):
    """
    Sample on_disconnect function.
    Handles lost connections.
    """
    logging.info("Lost connection to {}".format(client.addrport()))
    CLIENT_LIST.remove(client)

def cd_command(client, line):
    if len(line.split(' ')) < 2:
        client.pwd = client.container.exec_run("/bin/sh -c 'echo $HOME'").decode("utf-8")[:-1]
        return
    dir = line.split(' ')[1]
    response = client.container.exec_run("ls {}".format(dir)).decode("utf-8")
    if "No such file or directory" in response:
        client.send("sh: cd: can't cd to {}\n".format(dir))
    else:
        client.pwd = dir
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
    logging.info("{}: '{}'".format(client.addrport(), msg))
    client.send("{}\n".format(msg))
    if '||' in msg:
        logical_operator(client, msg)
        return
    msg = msg.split(';');
    for message in msg:
        cmd = message.split(' ')[0]
        if cmd == "cd":
            cd_command(client, message)
        elif cmd not in BLACK_LIST:
            newcmd = '/bin/sh -c "cd ' + client.pwd + ' && ' + message + '"'
            print(newcmd)
            response = client.container.exec_run(newcmd)
            response = response.decode("utf-8")
            print(response)
            if "exec failed" not in response:
                client.send(response)
            else:
                not_found(client, cmd)
        else:
            not_found(client, cmd)
        if message == 'quit':
            client.active = False
    return_prompt(client)

def logical_operator(client, msg):
    msg = msg.split('||')
    exit_status = 1;
    for message in msg:
        if exit_status == 0:
            break
        message = message.strip().split(';')
        for line in message:
            print(cmd)
            response = client.container.exec_run(cmd).decode("utf-8")
            if "can't open" in response:
                exit_status = 0;
            if "exec failed" not in response:
                client.send(response)
            else:
                not_found(client, line.split(' ')[0])
            print(response)

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
