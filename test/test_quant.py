import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

class QuantTest(unittest.TestCase):
    def assert_prop_true(self, prop):
        pred = pecan_parser.parse(prop).defs[0].body
        self.assertTrue(spot.dualize(pred.evaluate(Program([]))).is_empty())

    def assert_prop_false(self, prop):
        pred = pecan_parser.parse(prop).defs[0].body
        self.assertTrue(pred.evaluate(Program([])).is_empty())

    def test_exists_true(self):
        self.assert_prop_true('p() := forall x. exists y. x = y')

    def test_exists_true(self):
        self.assert_prop_false('p() := exists x. forall y. x = y')

    def test_forall_many(self):
        self.assert_prop_true('p() := forall x. forall y. forall z. (x = y) => (x = y | x = z)')

