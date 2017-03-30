from tests.dummy import *
from engine.cmd import *
from contextlib import contextmanager
import sys
import io
import unittest
import os
from patterns.patterns import build_list, dump_list, check_list
import warnings



@contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Scripted_Command_Testing(unittest.TestCase):
    def setUp(self):
        """
        Set up a new patternfile and instantiate a new
        dummy server and dummy client.
        """
        self.server = DummyTelnetServer()
        self.client = DummyTelnetClient()
        """
        This next line keeps unittest from displaying ResourceWarning
        due to the Docker module not properly closing out a socket.
        """
        warnings.simplefilter("ignore", ResourceWarning)


    def tearDown(self):
       """
       Rm -f the client's container and
       delete the patternfile.
       """
       self.client.cleanup()


    def run_it(self, msg):
        with captured_output() as (out, err):
            run_cmd(self.server, self.client, msg)
        output = out.getvalue().strip()
        output = output.split('\n')
        return (output)


    def test_echo_cmd(self):
        """
        Tests that a normal echo will respond
        as expected.

        Should probably add a little more
        to test variable expansion, etc.
        """
        msg = ["echo hello there"]
        arguments = ' '.join(msg[0].split(' ')[1:])
        output = self.run_it(msg)
        self.assertEqual(output[0], arguments)
        self.assertEqual(self.client.exit_status, 0)

    def test_echo_e_cmd(self):
        """
        Verifies that echo -e will work the same as Busybox,
        since certain bots like to use this to identify
        Busybox machines.
        """
        msg = ["echo -e '\\164\\147\\146\\171\\141\\147'"]
        arguments = ' '.join(msg[0].split(' ')[1:])
        output = self.run_it(msg)
        self.assertEqual(output[0], "tgfyag")
        self.assertEqual(self.client.exit_status, 0)

    def test_cd_cmd(self):
        """
        Ensures that cd tracks our PWD properly and
        gives an appropriate error message on failure.
        """
        msg = ["cd /tmp/"]
        output = self.run_it(msg)
        self.assertEqual(output[0], self.server.prompt.strip())
        self.assertEqual(self.client.pwd, '/tmp')
        self.assertEqual(self.client.exit_status, 0)

        msg = ["cd /"]
        self.run_it(msg)
        self.assertEqual(self.client.pwd, '/')
        self.assertEqual(self.client.exit_status, 0)

        msg = ["cd /notafolder/"]
        output = self.run_it(msg)
        self.assertEqual(output[0], "sh: cd: can't cd to /notafolder/")
        self.assertNotEqual(self.client.exit_status, 0)



if __name__ == "__main__":
    unittest.main()
