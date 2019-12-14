import unittest

from pecan.lang.optimizer.tools import *
from pecan.lang.ir import *
from pecan.lang.parser import pred_parser
from pecan.lang.ast_to_ir import ASTToIR

def expr_str(s):
    return ASTToIR().transform(pred_parser.parse(s))

class OptimizerToolsTest(unittest.TestCase):
    def test_depth_simple(self):
        self.assertEqual(DepthAnalyzer().count(expr_str('a + b')), 1)

    def test_depth_shallow(self):
        self.assertEqual(DepthAnalyzer().count(expr_str('a')), 0)

    def test_depth_deep(self):
        self.assertEqual(DepthAnalyzer().count(expr_str('a + a + a + 0')), 3)

    def test_frequency_simple(self):
        res = {
            expr_str('a + a'): 2,
            expr_str('a'): 4,
            expr_str('b'): 2
        }
        self.assertEqual(ExpressionFrequency().count(expr_str('a + a = b & a + a = b')), res)

    def test_frequency_with_indexing(self):
        res = {
            expr_str('i + k'): 2,
            expr_str('i + k + n'): 1,
            expr_str('i'): 2,
            expr_str('k'): 2,
            expr_str('n'): 1
        }
        self.assertEqual(ExpressionFrequency().count(expr_str('F[i + k] = F[i + k + n]')), res)


