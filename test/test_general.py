import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

from pecan import program

class GeneralTest(unittest.TestCase):
    def run_file(self, filename):
        prog = program.load(filename, quiet=True)
        self.assertTrue(prog.evaluate().result.succeeded())

    def test_load_pred(self):
        self.run_file('examples/test_load_aut.pn')

    def test_arith_basic(self):
        self.run_file('examples/test_arith.pn')

    def test_sturmian_basic(self):
        self.run_file('examples/test_sturmian.pn')

    def test_quant_file(self):
        self.run_file('examples/test_quant.pn')

    def test_stdlib_imported(self):
        self.run_file('examples/test_stdlib_imported.pn')

    def test_import_works(self):
        self.run_file('examples/test_import.pn')

    def test_quant_restricted(self):
        self.run_file('examples/test_quant_restricted.pn')

