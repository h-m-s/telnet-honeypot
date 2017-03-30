from tests.dummy import *
from engine.cmd import *
from contextlib import contextmanager
import sys
import io
import unittest


@contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Basic_Client_Testing(unittest.TestCase):
    def setUp(self):
        self.server = DummyTelnetServer()
        self.client = DummyTelnetClient()
        """
        This next line keeps unittest from displaying ResourceWarning
        due to the Docker module not properly closing out a socket.
        """
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        self.client.cleanup()



"""
server = DummyTelnetServer()
client = DummyTelnetClient()
client.send("Hello")
server.return_prompt(client)
"""
