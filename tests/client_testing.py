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

    def tearDown(self):
        self.client.cleanup()


    def run_it(self, msg):
        with captured_output() as (out, err):
            run_cmd(self.server, self.client, msg)
        output = out.getvalue().strip()
        output = output.split('\n')
        return (output)


    def test_echo(self):
        msg = ["echo hello there"]
        arguments = ' '.join(msg[0].split(' ')[1:])
        output = self.run_it(msg)
        self.assertEqual(output[0], arguments)


    def test_echo_e(self):
        msg = ["echo -e '\\164\\147\\146\\171\\141\\147'"]
        arguments = ' '.join(msg[0].split(' ')[1:])
        output = self.run_it(msg)
        self.assertEqual(output[0], "tgfyag")

"""
server = DummyTelnetServer()
client = DummyTelnetClient()
client.send("Hello")
server.return_prompt(client)
"""
