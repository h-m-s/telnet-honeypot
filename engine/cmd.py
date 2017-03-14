import re
import sys

SCRIPTED = ["dd", "rm", "exit"]
NOT_FOUND = ["nc", "shell"]
BLACK_LIST = ["sh", "chmod", "docker"]

def rm_cmd(client, line):
        """
        Instead of deleting stuff, let's move it to tmp. Good stuff gets deleted sometimes!
        Would like to change this soon to just immediately copy it out of the container 
        and still actually remove it, unless it's an unchanged file.
        """
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

def cd_cmd(client, line):
        """
        We can't actually move directories in the container, so CD has to keep track of the PWD
	on our side. Sort of ridiculous... but it works!
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

def dd_cmd(client, line):
        """
        This dd is sorta hackish.
        Sends back the proper response... for a 32 bit ARM system.
        Mirai and Hajime like this a lot more than a 64 bit setup.
        Planning on adding more configurable choices soon.
        """
        header = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"
        client.send(header)
        client.send("+10 records in\r\n1+0 records out\n")
        logger.info(header)
        logger.info("+10 records in\r\n1+0 records out\n")

def exit_cmd(client, line):
	"""
	Sets the client to being inactive so they'll be booted
	during the server master loop.
	"""
	client.active = False

def run_cmd(server, client):
        """
        Evaluates commands! First splits off logical operators.
	Logical operators are sorta wimpy right now. I haven't
	found a good, easy solution to get $? every time a command runs,
	but as soon as I do it'll be a fair bit more robust.
        Cat is the main command Mirai and Hajime seem to use in their logical
	operator test statements, and I've also seen rm, both are supported.

	Also completely ignores parentheses, and I'd like to tackle that next.
        """
        msg = [client.get_command()]
        print(msg)
        if not client.username or not client.password:
                server.login_screen(client, msg)
                return
        server.logger.info("COMMAND: {}: '{}'".format(client.addrport(), msg))
        if re.findall("(.*)\|\|(.*)", msg[0]):
                msg = re.findall("(.*)\|\|(.*)", msg[0])[0]
        for line in msg:
                line = line.strip().split(';')
                for command in line:
                        execute_cmd(client, server, command)
                if client.exit_status != 0:
                        break
        server.return_prompt(client)

def execute_cmd(client, server, msg):
        """
        This is an attempt to split run_cmd up a little.
        Handling parantheses and logical operators need a lot of loops!
        """
        msg = msg.strip()
        if msg == "":
                return
        cmd = msg.strip().split(' ')[0]
        if cmd in SCRIPTED:
                method = getattr(sys.modules[__name__], "{}_cmd".format(cmd))
                result = method(client, msg)
        elif cmd not in NOT_FOUND and cmd not in BLACK_LIST:
                response = "\n".join(client.run_in_container(msg)) + "\n"
                if "exec failed" not in response:
                        if response == "\n":
                                return
                        server.logger.info(response)
                        client.send(response)
        else:
                not_found(client, cmd)
