SCRIPTED = ["dd", "cd"]
NOT_FOUND = ["nc", "shell"]
BLACK_LIST = ["sh", "chmod", "docker"]

def rm_command(client, line):
    try:
        target = line.split(' ')[1].strip()
    except:
        client.send(client.container.exec_run("/bin/sh -c rm").decode("utf-8"))
        return
    response = client.container.exec_run("/bin/sh -c cd {} && test -f {} && echo 0".format(client.pwd, target)).decode("utf-8").strip()
    if response != "0":
        response = client.container.exec_run("/bin/sh -c cd {} && rm {}".format(client.pwd, target))
        print(response)
        client.send(response)
    else:
        client.container.exec_run("/bin/sh -c cd {} && cp {} /tmp/".format(client.pwd, target))
        client.container.exec_run("/bin/sh -c cd {} && rm {}".format(client.pwd, target))

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

def run_cmd(server, client):
    """
    evaluate commands!
    """
    msg = client.get_command()
    if not client.username or not client.password:
        server.login_screen(client, msg)
        return
    if msg == "":
        server.return_prompt(client)
        return
    server.logger.info("{}: '{}'".format(client.addrport(), msg))
    if '||' in msg:
        logical_operator(client, msg)
        server.return_prompt(client)
        return
    msg = msg.split(';');
    for message in msg:
        cmd = message.strip().split(' ')[0]
        print("cmd: " + str(cmd))
        if cmd == "cd":
            cd_command(client, message)
        if cmd[0] == ".":
            continue
        elif cmd == "dd":
            dd_command(client)
        elif cmd == "rm":
            rm_command(client, message)
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
            if "syntax error" in response:
                continue
            elif "exec failed" not in response:
                server.logger.info(response)
                client.send(response)
            else:
                not_found(client, cmd)
        elif cmd not in BLACK_LIST:
            not_found(client, cmd)
    server.return_prompt(client)

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
            print(message[j])
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
            if line in BLACK_LIST:
                return
            if "dd" in line[:2]:
                dd_command(client)
                continue
            if "cd" in line[:2]:
                cd_command(client, line)
                continue
            elif "rm" in line[:2]:
                rm_command(client)
                continue
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
