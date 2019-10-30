import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

class QuantTest(unittest.TestCase):
    def assert_prop_true(self, prop):
        pred = pecan_parser.parse(prop).defs[0]
        self.assertTrue(spot.dualize(pred.evaluate(Program([]))).is_empty())

    def assert_prop_false(self, prop):
        pred = pecan_parser.parse(prop).defs[0]
        self.assertTrue(pred.evaluate(Program([])).is_empty())

    def test_exists_true(self):
        self.assert_prop_true('forall x. exists y. x = y')

    def test_exists_true(self):
        self.assert_prop_false('exists x. forall y. x = y')

    def test_forall_many(self):
        self.assert_prop_true('forall x. forall y. forall z. (x = y) => (x = y | x = z)')

    def run_file(self, filename):
        with open(filename, 'r') as f:
            prog = pecan_parser.parse(f.read())

        prog.parser = pecan_parser
        prog.quiet = True

        self.assertTrue(prog.evaluate().result.succeeded())

    def test_quant_file(self):
        self.run_file('examples/quant-tests.pn')

