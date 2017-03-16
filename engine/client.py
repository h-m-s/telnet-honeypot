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

    def run_in_container(self, line):
        newcmd = '/bin/sh -c "cd {} && {};echo EXIT: $?"'.format(self.pwd, line)
        result = self.container.exec_run(newcmd).decode("utf-8", "replace").split('\n')
        print(result)
        return(result[:-2])

    def cleanup_container(self):
        if self.container.diff() != None:
            for difference in self.container.diff():
                md5 = self.container.exec_run("md5sum {}".format(difference['Path'])).decode("utf-8")
                md5 = md5.split(' ')[0]
                fname = "{}-{}-{}".format(str(time.isotime()).replace(" ", ""), md5, difference['Path'].split('/')[-1])
                logger.info("Saving file {} with md5sum {} from {}".format(difference['Path'], md5, self.addrport()))
                with open("./logs/{}.tar".format(fname), "bw+") as f:
                    strm, stat = self.container.get_archive(difference['Path'])
                    f.write(strm.data)
        self.container.remove(force=True)
