import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

class ArithTest(unittest.TestCase):
    def print_addition(self):
        prop = "1+1=2"
        pred = pecan_parser.parse(prop)
        print(pred.evaluate(Program([])))

    def test_undetermined(self):
        print(UndeterminedExpression("adder", [IntConst(1), IntConst(2), VarRef("a")], "a").evaluate(Program([])))
