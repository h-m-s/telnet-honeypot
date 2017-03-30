from threading import Thread
import threading
from engine.cmd import run_cmd

class CommandThread(Thread):
    def __init__(self, client, server, name):
        super().__init__()
        self.client = client
        self.server = server

    def run(self):
        while len(self.client.active_cmds) > 0:
            self.server.threadlock.acquire()
            msg = [self.client.active_cmds.pop()]
            self.server.threadlock.release()
            run_cmd(self.server, self.client, msg)
        self.client.active_cmds = []
        self.server.threads[self.client.ip] = None
