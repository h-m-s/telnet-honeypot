from engine.server import HoneyTelnetServer
from engine.client import HoneyTelnetClient
import unittest
import docker
import uuid
import logging

class DummyTelnetServer(HoneyTelnetServer):
    def __init__(self):
        self.client_list = []
        self.logger = logging.getLogger('TEST')


class DummyTelnetClient(HoneyTelnetClient):
    def __init__(self):
        self.dclient = docker.from_env()
        self.container = self.dclient.containers.run(
            "busybox", "/bin/sh",
            detach=True,
            tty=True,
            environment=["SHELL=/bin/sh"])
        self.pwd = "/"
        self.input_list = []
        self.active_cmds = []
        self.username = "test"
        self.password = "user"
        self.exit_status = 0
        self.uuid = uuid.uuid4()
        self.ip = "127.0.0.1"
        self.mode = "telnet"

    def send(self, line):
        print(line)

    def cleanup(self):
        self.container.remove(force=True)
