from threading import Thread
import threading
from engine.cmd import run_cmd

class CommandThread(Thread):
    def __init__(self, client, server, name):
        """
        Command thread is just a super simple threading setup
        to run individual client commands in.

        This means that if one client's input hangs, everyone else
        should be A-OK.

        TODO: Would really like to stream the output from the container so
        we can snag any available output on every server loop, because right now
        the thread has to finish before output is made available.

        Also need to ensure that if a client disconnects while a thread is still active,
        that the thread finishes up and the container is closed after the thread finishes.
        """
        super().__init__()
        self.client = client
        self.server = server

    def run(self):
        """
        Super simple loop for the command thread.
        Client.active_cmds is a list of commands for the thread,
        and we'll loop over this so if you spam with long-running commands, the thread
        will keep churning output instead of ignoring anything entered
        while a command is currently running.
        """
        while len(self.client.active_cmds) > 0:
            self.server.threadlock.acquire()
            msg = [self.client.active_cmds.pop()]
            self.server.threadlock.release()
            run_cmd(self.server, self.client, msg)
        self.client.active_cmds = []
        self.server.threads[self.client.uuid] = None
