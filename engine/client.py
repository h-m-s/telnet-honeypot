#!/usr/bin/env python3
import docker
import uuid
import time
from miniboa.telnet import TelnetClient
from threading import Thread
import os

class HoneyTelnetClient(TelnetClient):
    def __init__(self, sock, addr_tup):
        super().__init__(sock, addr_tup)
        self.dclient = docker.from_env()
        self.container = self.dclient.containers.run(
            "busybox", "/bin/sh",
            detach=True,
            tty=True,
            environment=["SHELL=/bin/sh"])
        self.pwd = "/"
        self.input_list = []
        self.active_cmds = []
        self.username = None
        self.password = None
        self.exit_status = 0
        self.uuid = uuid.uuid4()
        self.ip = self.addrport().split(":")[0]

    def cleanup_container(self, server):
        """
        Cleans up a container.
        Checks the difference between the base image and the container status.
        folder for analysis.
        """
        if self.container.diff() is not None:
            for difference in self.container.diff():
                result = self.container.exec_run(
                    '/bin/sh -c "test -d {} || echo NO"'.format(
                        difference['Path']))
                if "NO" in str(result):  # If echo 'NO' runs, file is not a dir
                    md5 = self.container.exec_run("md5sum {}".format(
                        difference['Path'])).decode("utf-8")
                    md5 = md5.split(' ')[0]
                    fname = "{}-{}".format(md5, difference['Path'].split('/')[-1])
                    if md5 == "d41d8cd98f00b204e9800998ecf8427e":
                        server.logger.info(
                            "Not saving empty file {} from {}.".
                            format(difference['Path'], self.ip))
                        continue
                    if os.path.isfile("./logs/{}.tar".format(fname)):
                        server.logger.info(
                            "Not saving duplicate file {} from {}.".
                            format(difference['Path'], self.ip))
                        continue
                    server.logger.info(
                        "Saving file {} with md5sum {} from {}".
                          format(difference['Path'], md5, self.ip))
                    with open("./logs/{}.tar".format(fname), "bw+") as f:
                        strm, stat = self.container.get_archive(
                            difference['Path'])
                        f.write(strm.data)
        self.container.remove(force=True)

    def run_in_container(self, line):
        """
        Takes in a command (pre-parsed/sanitized) and runs it in the client's
        container. Sorta hacky way to get the exit code, and I'm super open
        to suggestions on how else this could be done. The container doesn't
        actually exit (it's running the whole time the client is,
        detached) but does it even need to be running since I'm doing
        it this way anyways?
        """
        newcmd = '/bin/sh -c "cd {} && {};export LAST=$?"'.format(self.pwd, line)
        result = self.container.exec_run(newcmd).decode(
            "utf-8", "replace").split('\n')
        final = []
        for line in result:
            if "EXIT:" in line:
                try:
                    self.exit_status = int(line.split(":")[1].strip())
                except:
                    self.exit_status = 127
            elif line != "\n":
                final += [line]
        return("\n".join(final))
