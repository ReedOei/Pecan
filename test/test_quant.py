import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

class QuantTest(unittest.TestCase):
    def test_exists_true(self):
        pred = Forall('x', Exists('y', Equals(VarRef('x'), VarRef('y'))))
        evaluated = pred.evaluate(Program([]))
        self.assertTrue(spot.dualize(evaluated).is_empty())

    def test_exists_true(self):
        pred = Exists('x', Forall('y', Equals(VarRef('x'), VarRef('y'))))
        evaluated = pred.evaluate(Program([]))
        self.assertTrue(evaluated.is_empty())

    def test_forall_many(self):
        pred = Forall('x', Forall('y', Forall('z', Implies(Equals(VarRef('x'), VarRef('y')), Disjunction(Equals(VarRef('x'), VarRef('y')), Equals(VarRef('x'), VarRef('z')))))))
        evaluated = pred.evaluate(Program([]))
        self.assertTrue(spot.dualize(evaluated).is_empty())

