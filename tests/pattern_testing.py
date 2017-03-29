from tests.dummy import *
from engine.cmd import *
from contextlib import contextmanager
import sys
import io
import unittest
import os
from patterns.patterns import build_list, dump_list, check_list

@contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Pattern_Testing(unittest.TestCase):
    def setUp(self):
        """
        Set up a new patternfile and instantiate a new
        dummy server and dummy client.
        """
        self.patternfile = "patterns.json.test"
        if os.path.exists(self.patternfile):
            os.remove(self.patternfile)
        self.server = DummyTelnetServer()
        self.client = DummyTelnetClient()

    def tearDown(self):
       """
       Rm -f the client's container and
       delete the patternfile.
       """
       self.client.cleanup()
       if os.path.exists(self.patternfile):
            os.remove(self.patternfile)

    def test_new_patternfile(self):
       """
       Tests to make sure build_list will initialize an empty dict
       and dump_list will properly dump it as an empty list.
       """
       pattern_list = build_list(self.patternfile)
       self.assertEqual(pattern_list, {})
       dump_list(pattern_list, self.patternfile)
       self.assertTrue(os.path.exists(self.patternfile))
       with open(self.patternfile, "r") as f:
           self.assertEqual(f.read(), "{}")

    def test_patternfile_addition(self):
        """
        Tests to ensure that an client's input_list passed to
        check_list will properly ignore the first 2 commands
        (which should be username/pass), and that a second client
        with an identical input (with different username/pass)
        will be added to the same key, with both IPs listed as
        attackers.
        """
        pattern_list = build_list(self.patternfile)
        self.client.input_list = ["root", "toor", "echo hello"]
        check_list(self.client, self.server, self.patternfile)
        pattern_list = build_list(self.patternfile)
        self.assertEqual(len(pattern_list), 1)

        self.client.ip = "192.168.10.10"
        self.client.input_list = ["toor", "root", "echo hello"]
        check_list(self.client, self.server, self.patternfile)
        pattern_list = build_list(self.patternfile)
        self.assertEqual(len(pattern_list), 1)
        for key in pattern_list.keys():
            self.assertTrue(self.client.ip in pattern_list[key]['attackers'])
            self.assertTrue("127.0.0.1" in pattern_list[key]['attackers'])
            self.assertTrue("192.168.10.10" in pattern_list[key]['attackers'])
            self.assertTrue("root" not in pattern_list[key]['input'])
            self.assertTrue("toor" not in pattern_list[key]['input'])
            self.assertTrue("echo hello" in pattern_list[key]['input'])
            self.assertTrue(pattern_list[key]['downloads'] == [])

    def test_good_ip_parsing(self):
        """
        Ensures that any 4 groups of 1-3 digits will be treated as an IP.
        IPs in client input should be translated to 1.1.1.1 for the pattern list
        (in order to ensure that even if the C&C server/file host is different,
        the pattern will be treated the same).

        Also checks to ensure that download IPs stripped are added to the
        'downloads' key.
        """
        pattern_list = build_list(self.patternfile)
        self.client.input_list = ["root", "toor", "wget http://8.8.8.8"]
        check_list(self.client, self.server, self.patternfile)
        pattern_list = build_list(self.patternfile)
        self.assertEqual(len(pattern_list), 1)
        for key in pattern_list.keys():
            self.assertTrue("8.8.8.8" in pattern_list[key]['downloads'])
        self.client.input_list = ["toor", "root", "wget http://2.123.211.123"]
        check_list(self.client, self.server, self.patternfile)
        pattern_list = build_list(self.patternfile)
        self.assertEqual(len(pattern_list), 1)
        for key in pattern_list.keys():
            self.assertTrue("8.8.8.8" not in pattern_list[key]['input'])
            self.assertEqual(["wget http://1.1.1.1"], pattern_list[key]['input'])

    def test_non_ip_parsing(self):
        """
        Ensures that period delimited sequences of numbers not in 4 groups of
        1-3 won't be treated as IP numbers.

        Currently does not try to validate IPs, aka, does not care if the number
        is over 255.
        """
        pattern_list = build_list(self.patternfile)
        self.client.input_list = ["root", "toor", "wget http://72.88"]
        check_list(self.client, self.server, self.patternfile)
        pattern_list = build_list(self.patternfile)
        self.assertEqual(len(pattern_list), 1)
        self.client.input_list = ["toor", "root", "wget http://12312312.123"]
        check_list(self.client, self.server, self.patternfile)
        pattern_list = build_list(self.patternfile)
        self.assertEqual(len(pattern_list), 2)
        for key in pattern_list.keys():
            self.assertTrue("1.1.1.1" not in pattern_list[key]['input'])


if __name__ == "__main__":
    unittest.main()
