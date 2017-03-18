import re
import sys

SCRIPTED = ["dd", "rm", "exit", "cd", "cat"]
NOT_FOUND = ["nc", "shell"]
BLACK_LIST = ["sh", "chmod", "docker"]


def rm_cmd(server, client, line):
        """
        Instead of deleting stuff, let's move it to tmp. Good stuff gets
        deleted sometimes! Would like to change this soon to just
        immediately copy it out of the container.
        """
        try:
                target = line.split(' ')[1].strip()
        except:
                client.send(client.container.exec_run("/bin/sh -c rm")
                            .decode("utf-8"))
                return
        response = client.container.exec_run(
                "/bin/sh -c cd {} && test -f {} && echo 0"
                .format(client.pwd, target)).decode("utf-8").strip()
        if response != "0":
                response = client.container.exec_run(
                        "/bin/sh -c cd {} && rm {}".format(client.pwd, target))
                client.send(response)
        else:
                client.container.exec_run("/bin/sh -c cd {} && cp {} /tmp/"
                                          .format(client.pwd, target))
                client.container.exec_run("/bin/sh -c cd {} && rm {}"
                                          .format(client.pwd, target))


def dd_cmd(server, client, line):
        """
        This dd is sorta hackish.
        Sends back the proper response... for a 32 bit ARM system.
        Mirai and Hajime like this a lot more than a 64 bit setup.
        Planning on adding more configurable choices soon.
        """
        header = ("\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00 \
        \x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00 \
        \x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00 \
        \x1b\x00\x1a\x00")
        client.send(header)
        client.send("+10 records in\r\n1+0 records out\n")


def exit_cmd(server, client, line):
        """
        Sets the client to being inactive so they'll be booted
        during the server master loop.
        """
        client.active = False


def cd_cmd(server, client, line):
    """
    Sorta hackish cd command. Keeps track of where we're cding to, to keep
    track of the client's PWD.
    """
    if len(line.split(' ')) < 2:
            client.pwd = client.container.exec_run(
                    "/bin/sh -c 'echo $HOME'").decode("utf-8")[:-1]
            return
    dir = line.split(' ')[1]
    response = client.container.exec_run(
            '/bin/sh -c "cd ' + client.pwd + ';cd ' + dir + ';pwd' '"').decode(
                    "utf-8")
    if "can't cd" in response:
            client.send("sh: cd: can't cd to {}\n".format(dir))
            server.logger.info("sh: cd: can't cd to {}\n".format(dir))
    else:
            client.pwd = response[:-1]
            if (len(client.pwd) > 2) and client.pwd[-1] == '/':
                    client.pwd = client.pwd[:-1]


def cat_cmd(server, client, line):
        """
        Super hacky workaround for /proc/mounts. Need a real solution here,
        ultimately would like to create a command for making custom Docker
        images with files pre-replaced!
        """
        if len(line.split(' ')) > 1 and line.split(' ')[1] == "/proc/mounts":
                with open("./fakefiles/proc%mounts", "r") as f:
                        response = f.read()
        else:
                response = client.run_in_container(line)
        client.send(response)


def run_cmd(server, client):
        """
        Evaluates commands! First splits off logical operators.

        Parentheses and logical operators are still kinda
        iffy, but work enough for
        the simple stuff the common bots try. :)
        """
        msg = [client.get_command()]
        if not client.username or not client.password:
                server.login_screen(client, msg)
                return
        server.logger.info("COMMAND: {}: '{}'".format(
                client.addrport(), msg[0]))
        loop_cmds(server, client, msg[0].split(';'))
        server.return_prompt(client)

def loop_cmds(server, client, msg):
        if re.findall("\(([^)]*)\)", msg[0]) is not None:
                print(re.findall("\(([^)]*)\)", msg[0]))
        if re.findall("(.*)\|\|(.*)", msg[0]) is not None:
                print(re.findall("(.*)\|\|(.*)", msg[0]))
        for line in msg:
                print("Running command: {}".format(line))
                execute_cmd(client, server, line)
        if client.exit_status != 0:
                pass

def execute_cmd(client, server, msg):
        """
        This is an attempt to split run_cmd up a little.
        Commands should already be parsed before getting here, and this
        just be used to handle a single command and its arguments.
        """
        msg = msg.strip()
        if msg == "":
                return
        cmd = msg.strip().split(' ')[0]
        if cmd in SCRIPTED:
                method = getattr(sys.modules[__name__], "{}_cmd".format(cmd))
                result = method(server, client, msg)
        elif cmd not in NOT_FOUND and cmd not in BLACK_LIST:
                response = client.run_in_container(msg)
                if "exec failed" not in response:
                        if response == "\n":
                                return
                        server.logger.info(response)
                        client.send(response)
        else:
                not_found(client, cmd)
