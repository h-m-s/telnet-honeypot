#!/usr/bin/env python3
import docker
import uuid
import time
from miniboa.telnet import TelnetClient
from threading import Thread
import os
import json
from models import storage
from models.malware_files import MalwareFile

class HoneyTelnetClient(TelnetClient):
    def __init__(self, sock, addr_tup, server):
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
        self.container = server.dclient.containers.run(
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
        self.files = []
        self.server = server

    def cleanup_container(self, server):
        """
        Cleans up a container.

        Checks for any changes, and then stops/removes it.
        """
        try:
            self.check_changes(server)
            self.server.APIClient.remove_container(self.container.id, force=True)
            if server.postgres == True:
                self.store_files()
        except:
            return

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

        Should we check against db and not save if matching md5 in db?
        """
        md5 = self.container.exec_run("md5sum {}".format(
            filepath)).decode("utf-8")
        if 'No such file' in md5:
            return
        md5 = md5.split(' ')[0]
        file_name = filepath.split('/')[-1]
        for malware_file in self.files:
            if malware_file['md5'] == md5 and malware_file['file_name'] == file_name:
                return
        self.files += [{'md5': md5, 'file_name': file_name}]
        fname = "{}-{}".format(md5, file_name)
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

    def store_files(self):
        for malware in self.files:
            query = storage.session.query(MalwareFile).filter(
                MalwareFile.file_md5 == malware['md5'])
            if query.count() != 0:
                malware_file = query.all()[0]
                malware_file.count += 1
                try:
                    alt_names = json.loads(malware_file.alternative_names)
                except Exception as err:
                    print("Issue loading json for {}: {}".format(malware_file.md5, err))
                if malware_file.file_name != malware['file_name']:
                    if malware['file_name'] not in alt_names:
                        alt_names += [malware['file_name']]
                malware_file.alternative_names = json.dumps(alt_names)
                servers = json.loads(malware_file.servers)
            else:
                malware_file = MalwareFile(malware['file_name'], malware['md5'])
            malware_file.save()

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
        self.exec = self.server.APIClient.exec_create(self.container.id, newcmd)
        result = self.server.APIClient.exec_start(self.exec['Id']).decode(
          "utf-8", "replace")
        self.exit_status = self.server.APIClient.exec_inspect(self.exec['Id'])['ExitCode']
        return(result)
