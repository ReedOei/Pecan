import unittest

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

class ParserTest(unittest.TestCase):
    def test_pred(self):
        ast = [Equals(VarRef('x'), VarRef('x'))]
        self.assertEqual(repr(ast), repr(pecan_parser.parse('x = x')))

    def test_forall(self):
        ast = [Forall('x', Implies(Equals(Add(VarRef('x'), VarRef('y')), Index('C', VarRef('i'))), Equals(Index('C', VarRef('i')), IntConst(2))))]
        self.assertEqual(repr(ast), repr(pecan_parser.parse('forall x.x + y = C[i] => C[i] = 2')))

    def test_exists(self):
        ast = [Exists('y', Exists('z', Equals(Sub(VarRef('y'), IntConst(1)), Sub(VarRef('z'), IntConst(2)))))]
        self.assertEqual(repr(ast), repr(pecan_parser.parse('exists y. exists z. y - 1 = z - 2')))

    def test_complicated(self):
        ast = [Forall('alpha', Conjunction(Disjunction(Equals(VarRef('x'), VarRef('alpha')), GreaterEquals(VarRef('z'), VarRef('k'))),
                                          Iff(LessEquals(Add(Add(VarRef('x'), VarRef('z')), Sub(VarRef('x'), IntConst(1))),
                                                         IntConst(7)),
                                              Less(Index('C', Add(VarRef('i'), VarRef('k'))), IntConst(1)))))]
        self.assertEqual(repr(ast), repr(pecan_parser.parse('A alpha. (x = alpha | z >= k) and ((((x + z) + (x - 1)) <= 7) <=> (C[i + k] < 1))')))

