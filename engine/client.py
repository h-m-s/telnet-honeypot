#!/usr/bin/env python3
import docker
import uuid
import time
from miniboa.telnet import TelnetClient
from threading import Thread
import os

class HoneyTelnetClient(TelnetClient):
<<<<<<< HEAD
    def __init__(self, sock, addr_tup, server):
=======
    def __init__(self, sock, addr_tup):
>>>>>>> 59174f8820a71017eb4786ccd0a8ad1464e3c983
        """
        The HoneyTelnetClient is the actual client handler for telnet connections.

        Quick overview:
            dclient: Docker client
            APIClient: Docker low-level api client
            container: Docker container associated with client
            pwd: client PWD in container
            input_list: list of all input, exactly as entered, for pattern recognition
            active_cmds: queue for threads
            username: username used to log in
            password: password used to log in
            exit_status: last exit status
            uuid: uuid for client
            passwd_flag: checks to see if we're in the middle of passwd
            ip: client ip
        """
        super().__init__(sock, addr_tup)
<<<<<<< HEAD
        self.container = server.dclient.containers.run(
=======
        self.dclient = docker.from_env()
        self.APIClient = docker.APIClient(base_url='unix://var/run/docker.sock')
        self.container = self.dclient.containers.run(
>>>>>>> 59174f8820a71017eb4786ccd0a8ad1464e3c983
            "honeybox", "/bin/sh",
            detach=True,
            tty=True,
            environment=["SHELL=/bin/sh"])
        self.pwd = "/"
        self.input_list = []
        self.active_cmds = []
        self.username = None
        self.password = None
        self.exit_status = 0
        self.uuid = str(uuid.uuid4())
        self.passwd_flag = None
        self.ip = self.addrport().split(":")[0]
        self.server = server

    def cleanup_container(self, server):
        """
        Cleans up a container.

        Checks for any changes, and then stops/removes it.
        """
        self.check_changes(server)
<<<<<<< HEAD
        self.server.APIClient.remove_container(self.container.id, force=True)
        
=======
        self.APIClient.remove_container(self.container.id, force=True)

>>>>>>> 59174f8820a71017eb4786ccd0a8ad1464e3c983
    def check_changes(self, server):
        """
        Checks for the difference between the container's base image and the
        current state of the container and sends any new/changed files off to
        save_file.
        """
        if self.container.diff() is not None:
            for difference in self.container.diff():
                result = self.container.exec_run(
                    '/bin/sh -c "test -d {} || echo NO"'.format(
                        difference['Path']))
                if "NO" in str(result):  # If echo 'NO' runs, file is not a dir
                    self.save_file(server, difference['Path'])


    def save_file(self, server, filepath):
        """
        Grabs an MD5 of a file and decides if we're going to save it or not.

        If we're going to save it, it'll be TAR'd up and saved in /logs/.
        """
        md5 = self.container.exec_run("md5sum {}".format(
            filepath)).decode("utf-8")
        md5 = md5.split(' ')[0]
        fname = "{}-{}".format(md5, filepath.split('/')[-1])
        if os.path.isfile("./logs/{}.tar".format(fname)):
            server.logger.info(
                "[{}]: NOT SAVING DUPLICATE FILE: {}".
                format(self.addrport(), fname))
            return
        server.logger.info(
            "[{}]: SAVING FILE: {}".
            format(self.addrport(), fname))
        with open("./logs/{}.tar".format(fname), "bw+") as f:
            strm, stat = self.container.get_archive(filepath)
            f.write(strm.data)


    def run_in_container(self, line):
        """
        Takes in a command (already parsed/sanitized) and runs it in the client's
        container.

        Needs to use the low level APIClient in order to snag the exit code.
        The higher level client doesn't seem to allow to grab the exit code
        of the last exec (just the exit code of the container itself, if it stops)
        but it IS a lot friendlier. So right now we have to
        initialize both clients, which is not ideal. Should probably
        just drop the higher level client altogether.
        """
        newcmd = '/bin/sh -c "cd {} && {};exit $?"'.format(self.pwd, line)
<<<<<<< HEAD
        self.exec = self.server.APIClient.exec_create(self.container.id, newcmd)
        result = self.server.APIClient.exec_start(self.exec['Id']).decode(
          "utf-8", "replace")
        self.exit_status = self.server.APIClient.exec_inspect(self.exec['Id'])['ExitCode']
=======
        self.exec = self.APIClient.exec_create(self.container.id, newcmd)
        result = self.APIClient.exec_start(self.exec['Id']).decode(
          "utf-8", "replace")
        self.exit_status = self.APIClient.exec_inspect(self.exec['Id'])['ExitCode']
>>>>>>> 59174f8820a71017eb4786ccd0a8ad1464e3c983
        return(result)
