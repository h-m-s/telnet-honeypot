#!/usr/bin/env python3
import docker
import uuid
import time
from miniboa.telnet import TelnetClient


class HoneyTelnetClient(TelnetClient):
    def __init__(self, sock, addr_tup):
        super().__init__(sock, addr_tup)
        self.dclient = docker.from_env()
        self.container = self.dclient.containers.run(
            "busybox", "/bin/sh", detach=True, tty=True)
        self.pwd = "/"
        self.username = None
        self.password = None
        self.exit_status = 0
        self.uuid = uuid.uuid4()
        self.ip = self.addrport().split(":")[0]

    def run_in_container(self, line):
        """
        Takes in a command (pre-parsed/sanitized) and runs it in the client's
        container. Sorta hacky way to get the exit code, and I'm super open
        to suggestions on how else this could be done. The container doesn't
        actually exit (it's running the whole time the client is,
        detached) but does it even need to be running since I'm doing
        it this way anyways?
        """
        newcmd = '/bin/sh -c "cd {} && {};echo EXIT:$?"'.format(self.pwd, line)
        result = self.container.exec_run(newcmd).decode(
            "utf-8", "replace").split('\n')
        final = []
        for line in result:
            if "EXIT:" in line:
                print("EXIT LINE: {}".format(line))
                self.exit_status = line.split(":")[1]
            elif line != "\n":
                final += [line]
        return("\n".join(final))

    def cleanup_container(self):
        """
        Cleans up a container.
        Checks the difference between the base image and the container status.
        If any found, this will TAR all the changes and move them into the logs
        folder for analysis.
        """
        if self.container.diff() is not None:
            print(self.container.diff())
            for difference in self.container.diff():
                result = self.container.exec_run(
                    '/bin/sh -c "test -d {} && echo YES"'.format(
                        difference['Path']))
                if "YES" not in str(result):
                    md5 = self.container.exec_run("md5sum {}".format(
                        difference['Path'])).decode("utf-8")
                    md5 = md5.split(' ')[0]
                    fname = "{}-{}-{}".format(str(time.strftime('%m%d%H%M')),
                                              md5, difference['Path'].
                                              split('/')[-1])
                    print("Saving file {} with md5sum {} from {}".
                          format(difference['Path'], md5, self.addrport()))
                    with open("./logs/{}.tar".format(fname), "bw+") as f:
                        strm, stat = self.container.get_archive(difference['Path'])
                        f.write(strm.data)
        self.container.remove(force=True)
