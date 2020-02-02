#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from lark import Lark, Transformer, v_args

from pecan.lang.optimizer.tools import *
from pecan.lang.ir import *
from pecan.lang.parser import PecanTransformer
from pecan.lang.ast_to_ir import ASTToIR

from pecan.lang.optimizer.redundant_variable_optimizer import RedundantVariableOptimizer
from pecan.lang.optimizer.unused_variable_optimizer import UnusedVariableOptimizer

pred_parser = Lark.open('pecan/lang/lark/pecan_grammar.lark', parser='lalr', transformer=PecanTransformer(), propagate_positions=True, start='pred')

def expr_str(s):
    return ASTToIR().transform(pred_parser.parse(s))

class DummyOptimizer:
    def __init__(self):
        self.prog = None

def test_depth_simple():
    assert DepthAnalyzer().count(expr_str('a + b')) == 1

def test_depth_shallow():
    assert DepthAnalyzer().count(expr_str('a')) == 0

def test_depth_deep():
    assert DepthAnalyzer().count(expr_str('a + a + a + 0')) == 3

def test_frequency_simple():
    res = {
        expr_str('a + a'): 2,
        expr_str('a'): 4,
        expr_str('b'): 2
    }
    assert ExpressionFrequency().count(expr_str('a + a = b & a + a = b')) == res

def test_frequency_with_indexing():
    # Note that each count is double what appears below because the translation transform it into an IFF (see ASTToIR.transform_EqualsCompareIndex())
    res = {
        expr_str('i + k'): 4,
        expr_str('i + k + n'): 2,
        expr_str('i'): 4,
        expr_str('k'): 4,
        expr_str('n'): 2
    }
    assert ExpressionFrequency().count(expr_str('F[i + k] = F[i + k + n]')) == res

# TODO: Move this out, test other optimizers, add integration tests for optimizers
def test_redundant_variable_optimizer():
    changed, new_node = RedundantVariableOptimizer(DummyOptimizer()).optimize(expr_str('exists a. exists b. a = b & a + b = c'), None)

    assert changed
    assert new_node == expr_str('exists a. exists b. a = a & a + a = c')

def test_redundant_variable_no_change():
    changed, new_node = RedundantVariableOptimizer(DummyOptimizer()).optimize(expr_str('exists a. exists b. a <= b'), None)

    assert not changed
    assert new_node == expr_str('exists a. exists b. a <= b')

def test_unused_variable_optimizer():
    changed, new_node = UnusedVariableOptimizer(DummyOptimizer()).optimize(expr_str('exists x. a + b = c'), None)

    assert changed
    assert new_node == expr_str('a + b = c')

