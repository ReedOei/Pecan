import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

class QuantTest(unittest.TestCase):
    def run_file(self, filename):
        with open(filename, 'r') as f:
            prog = pecan_parser.parse(f.read())

        prog.parser = pecan_parser
        prog.quiet = True

        self.assertTrue(prog.evaluate().result.succeeded())

    def test_load_pred(self):
        self.run_file('examples/load_aut.pn')

