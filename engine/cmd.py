import re
1;4205;0cimport time
import sys
import os
import threading
from threading import Thread

SCRIPTED = ["rm", "exit", "cd", "cat", "echo", "reboot", "passwd", "sh", "dd"]
BLACK_LIST = ["docker", "nc"]
IGNORE = ["chmod", "shell", "sleep"]

def sh_cmd(server, client, line):
    """                                                                         
    Serves up the default message from Busybox                                  
    """

    banner = ("\n\nBusyBox v1.18.4 (2015-10-21 12:02:45 CST) built-in shell (as\h)\n"
              "Revision: 11734\n"
              "Enter 'help' for a list of built-in commands.\n\n")
    client.send(banner)
    return

def passwd_cmd(server, client, line):
        """
        Passwd command! Since we're not streaming output from the Docker
        containers (yet?), this is what we'll serve up for the passwd command.
        It does /not/ accept any passwd thrown in, and requires the same
        username/password used to login to the server.

        If password mode isn't set to True in the config file, this really
        doesn't do much, except allow us to capture the intended password.
       
        If password mode IS set to True, until this is ran, the server
        will accept any username/password given. Once a successful
        password change is made, the server will only allow logins
        from that specific username/password combo!

        This functionality is a response to a bot that has been found
        changing passwords to randomly generated ones, 
        in an effort to see if it'll actually return to use the same passwd.
        We want to make it look like the password change is successful
        just in case it tries to run the original login (or a different one)
        to verify that it successfully changed the password.
        """
        if not client.passwd_flag:
                client.passwd_flag = 1
        if client.passwd_flag == 1:
                response = ("Changing password for root.\n"
                            "(current) UNIX password: ")
        elif client.passwd_flag == 2:
                if client.input_list[-1] == client.password:
                        response = "New password: "
                else:
                        response = ("passwd: Authentication token manipulation"
                                    " error\npasswd: password unchanged\n")
                        client.passwd_flag = None
                        client.send(response)
                        return

        elif client.passwd_flag == 3:
                response = "Retype password: "
        elif client.passwd_flag == 4:
                if client.input_list[-1] == client.input_list[-2]:
                        response = ("passwd: password for root changed by root"
                                    "\n")
                        server.username = client.username
                        server.password = client.input_list[-1]
                else:
                        response = ("Passwords don't match\n"
                                    "passwd: password for root is unchanged\n")
                client.passwd_flag = None
        client.send(response)
        if client.passwd_flag:
                client.passwd_flag += 1


def rm_cmd(server, client, line):
        """
        This moves anything removed to /tmp/ before actually removing it.
        Right now we're overactively grabbing ANY changed files, on every
        line if input, so this might be overkill.
        """
        try:
                target = line.split(' ')[1].strip()
        except:
                client.send(client.container.exec_run("/bin/sh -c rm")
                            .decode("utf-8"))
                return
        client.run_in_container("test -f {}")
        if client.exit_status != "0":
                response = client.run_in_container(line)
                client.send(response)
                server.logger.debug(response)
        else:
                client.container.exec_run("/bin/sh -c 'cd {} && cp {} /tmp/'"
                                          .format(client.pwd, target))
                client.run_in_container(line)


def echo_cmd(server, client, line):
        """
        If we wanna masquerade as Busybox properly, our echo escapes
        need to be fixed. This is a quick fix for scripts that use
        the LizardSquad method of detecting if they're in a real Busybox
        machine or not, by echoing \\147\\141\\171\\146\\147\\164. Busybox
        will translate it to ASCII, sh/etc will just escape one backslash.
        """
        if line.split(' ')[1] == '-e' or line.split(' ')[1] == '-ne':
                line = line.replace('//', '/')
                line = line.replace('"', "'")
        server.logger.info(
            "[{}]: EXECUTING CMD: {}".format(
                client.addrport(), line.split(' ')[0]))
        response = client.run_in_container(line)
        if "exec failed" not in response:
            if response == "\n":
                return
            server.logger.debug(
                    "[{}]: RESPONSE: {}".format(client.addrport(), response[:-1]))
            client.send(response)
            server.logger.debug(
                client.exit_status)

def dd_cmd(server, client, line):
        """
        This command is tailored to Hajime, which uses dd to
        grab the ELF header of a file and snag arch info.

        Sends back the proper response for a 32 bit ARM system.
        Mirai and Hajime like this a lot more than a 64 bit response.
        Planning on adding more configurable choices soon.
        """
        
        header = ("\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00")
        client.send(header)
        client.send("52+0 records in\r\n52+0 records out\n")
        server.logger.info("[{}]: SENT FAKE DD".format(client.addrport()))
        client.exit_status = 0

def reboot_cmd(server, client, line):
        """
        Quick little reboot that waits a second and boots the client.
        """
        client.send("The system is going down for reboot NOW!\n")
        time.sleep(2)
        client.active = False


def exit_cmd(server, client, line):
        """
        Sets the client to being inactive so they'll be booted
        during the server master loop.
        """
        client.active = False


def cd_cmd(server, client, line):
    """
    Since we're not running a single exec, we need to keep track of where
    we want to CD off to.
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
        message = "sh: cd: can't cd to {}\n".format(dir)
        client.send(message)
        server.logger.debug(message)
        client.exit_status = -1

    else:
        client.exit_status = 0
        client.pwd = response[:-1]
        if (len(client.pwd) > 2) and client.pwd[-1] == '/':
            client.pwd = client.pwd[:-1]


def cat_cmd(server, client, line):
        """
        Cat workaround. Most files can be directly replaced in the Docker image,
        however there's some things this won't work for. Such as:

        echo/binaries: Obviously we could replace /bin/echo with an ARM32
        /bin/echo (not too many bots expecting a x64 binary), but unless
        this honeypot is built on an ARM32 system, that might run into some issues.
        Instead we'll just return a fake header. Originally I was storing a fake binary
        and returning the real cat output, but this actually works better!

        proc stuff: Obviously we can't overwrite /proc/mounts or cpuinfo,
        both super common targets for bots.
        """
        try:
                target = line.split(' ')[1]
        except:
                response = client.run_in_container(line)
                return client.send(response)
        if target == "/proc/mounts":
                path = os.path.dirname(os.path.realpath(__file__))
                path = path[:-7]  # shaves off /engine
                with open("{}/fakefiles/proc%mounts".format(path), "r") as f:
                        response = f.read()
                client.exit_status = 0
        elif target == "/proc/cpuinfo":
                path = os.path.dirname(os.path.realpath(__file__))
                path = path[:-7]  # shaves off /engine
                with open("{}/fakefiles/proc%cpuinfo".format(path), "r") as f:
                        response = f.read()
                client.exit_status = 0
        elif (target == "/bin/busybox" or target == "$SHELL" or
              target == "/bin/echo"):
                response = ("\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00"
                            "\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00"
                            "\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54"
                            "\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00"
                            "\x09\x00\x28\x00\x1b\x00\x1a\x00")
        else:
                response = client.run_in_container(line)
        client.send(response)


def run_cmd(server, client, msg):
        """
        Run_cmd is where input should start.
        
        Adds the commands ran, before being parsed, to the master input list
        (this is the list used to break activity down into patterns).
        
        Then, ensure they're 'logged in'.
        
        Then it'll start loop_cmds, which breaks off logical operators,
        and finally it'll check the container for changes and return the prompt.
        """
        client.input_list += msg
        server.logger.info("[{}]: RECEIVED INPUT: {}".format(client.addrport(), msg))
        if msg == [""]:
                server.logger.info("Ignoring empty input from {}".format(
                        client.ip))
                return
        if not client.username or not client.password:
                server.login_screen(client, msg)
                return
        loop_cmds(server, client, msg[0].split(';'))
        client.check_changes(server)
        server.return_prompt(client)


def loop_cmds(server, client, msg):
        """
        Loop cmd uses re to try to break off logical operators.

        Parentheses aren't fully supported right now, but it's been enough
        to handle the common bot traffic.

        Logical operators (or/and) should work just fine, however.
        """
        parentheses = 0
        for line in msg:
                line = line.strip()
                if line == "":
                        continue
                if line[0] == '(':
                        parentheses = 1
                        line = line[1:]
                if line[-1] == ')':
                        parentheses = 0
                        line = line[:-1]
                if len(re.findall("(.*)\|\|(.*)", line)) > 0:
                        reg = re.findall("(.*)\|\|(.*)", line)
                        for cmd in reg:
                                loop_cmds(server, client, [cmd[0]])
                                if (client.exit_status != 0):
                                        server.logger.debug(
                                                "EXIT NOT ZERO")
                                        print(cmd[1])
                                        loop_cmds(server, client, [cmd[1]])
                                else:
                                        print("Exit zero, breaking")
                                        return
                elif len(re.findall("(.*)&&(.*)", line)) > 0:
                        reg = re.findall("(.*)&&(.*)", line)
                        for cmd in reg:
                                loop_cmds(server, client, [cmd[0]])
                                if (client.exit_status == 0):
                                        server.logger.debug(
                                                "True, continuing.")
                                        loop_cmds(server, client, [cmd[1]])
                                else:
                                        continue
                else:
                        execute_cmd(client, server, line)


def execute_cmd(client, server, msg):
        """
        Last stop in the command loop.

        Decides what to do with the parsed command.

        Scripted commands will have the appropriate command ran,
        black listed commands will return 'not found',
        and ignored commands will simply return.

        Blacklisted commands are good for things like netcat,
        which may be installed by default, but security wise it's a bit easier
        just to deny access.

        Ignored commands are good for things like 'sh', where
        you want to prevent a new shell from actually opening, but if you just return
        the prompt it looks exactly like a new shell.

        If it's not in any of these, we'll run the client's run_in_container method.
        """
        cmd = msg.strip().split(' ')[0]
        if cmd[0] == "." or cmd in IGNORE:
                server.logger.info("[{}]: IGNORING COMMAND: {}".format(client.addrport(), cmd))
                return
        if 'busybox' in cmd:
                server.logger.info("[{}]: SCRIPTED CMD: busybox".format(
                        client.addrport(), cmd))
                busybox(server, client, msg)
                return
        if client.passwd_flag is not None:
                passwd_cmd(server, client, msg)
                return
        if cmd in SCRIPTED:
                server.logger.info(
                        "[{}]: SCRIPTED CMD: {}".format(
                                client.addrport(), cmd))
                method = getattr(sys.modules[__name__],
                                 "{}_cmd".format(cmd))
                result = method(server, client, msg)
        elif cmd not in BLACK_LIST and cmd not in IGNORE:
                server.logger.info(
                        "[{}]: EXECUTING CMD: {}".format(
                                client.addrport(), cmd))
                response = client.run_in_container(msg)
                if "exec failed" not in response:
                        if response == "\n":
                                return
                        server.logger.debug(
                                "[{}]: RESPONSE: \n{}".format(
                                        client.addrport(), response[:-1]))
                        client.send(response)
                        server.logger.debug(client.exit_status)
        else:
                not_found(client, server, cmd)


def not_found(client, server, command):
        """
        Defines the response to anything in the blacklist.
        """
        server.logger.info("[{}]: BLACKLIST: {}".format(client.addrport(), command))
        client.send("sh: {}: command not found\n".format(command))
        client.exit_status = 127


def busybox(server, client, command):
        """
        Wrapper for /bin/busybox so we can decide
        which commands run through /bin/busybox and which
        we script out.
        """
        not_accepted = ['nc', 'cat']
        if re.search(r'busybox ([A-Z]*)$', command, re.MULTILINE) or len(
                        command.split(' ')) == 1:
                response = client.run_in_container(command)
        else:
                try:
                        newcommand = command.split(' ')[1:]
                except:
                        response = client.run_in_container(command)
                        client.send(response)
                        return
                if newcommand[0] not in not_accepted:
                        response = client.run_in_container(command)
                else:
                        execute_cmd(client, server, ' '.join(newcommand))
                        return
        server.logger.debug(response)
        client.send(response)
