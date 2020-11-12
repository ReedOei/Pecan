#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.optimizer.boolean import BooleanOptimizer
from pecan.lang.optimizer.arithmetic import ArithmeticOptimizer
from pecan.lang.optimizer.cse import CSEOptimizer
from pecan.lang.optimizer.redundant_variable_optimizer import RedundantVariableOptimizer
from pecan.lang.optimizer.unused_variable_optimizer import UnusedVariableOptimizer
from pecan.lang.ir import *

from pecan.settings import settings

class UntypedOptimizer:
    def __init__(self, prog):
        self.prog = prog

    def optimize(self):
        for i, d in enumerate(self.prog.defs):
            if type(d) is NamedPred:
                self.prog.defs[i] = NamedPred(d.name, d.args, d.arg_restrictions, self.run_optimizations(d.body, d), restriction_env=d.restriction_env, arg_name_map=d.arg_name_map)

        return self.prog

    def run_optimizations(self, node, pred):
        settings.log(2, lambda: f'Optimizing: {node}')

        if settings.min_opt():
            optimization_pass = [ ArithmeticOptimizer(self), BooleanOptimizer(self) ]
        else:
            optimization_pass = [ ArithmeticOptimizer(self), BooleanOptimizer(self) ] # RedundantVariableOptimizer(self) ]

        settings.log(2, lambda: f'Optimization passes: {optimization_pass}')

        new_node = node

        ast_changed = True # Default to true so we run at least once
        while ast_changed:
            ast_changed = False
            for optimization in optimization_pass:
                changed, new_node = optimization.optimize(new_node, pred)
                ast_changed |= changed

        settings.log(2, lambda: f'Optimized node: {new_node}')

        return new_node

class Optimizer:
    def __init__(self, prog):
        self.prog = prog

    def optimize(self, pred):
        return NamedPred(pred.name, pred.args, pred.arg_restrictions, self.run_optimizations(pred.body, pred), restriction_env=pred.restriction_env, arg_name_map=pred.arg_name_map)

    def run_optimizations(self, node, pred):
        settings.log(2, lambda: f'Optimizing: {node}')

        if settings.min_opt():
            optimization_pass = [ ArithmeticOptimizer(self), BooleanOptimizer(self) ]
        else:
            # optimization_pass = [ ArithmeticOptimizer(self), CSEOptimizer(self), BooleanOptimizer(self), RedundantVariableOptimizer(self), UnusedVariableOptimizer(self) ]
            optimization_pass = [ ArithmeticOptimizer(self), CSEOptimizer(self), BooleanOptimizer(self), UnusedVariableOptimizer(self) ]

        settings.log(2, lambda: f'Optimization passes: {optimization_pass}')

        new_node = node

        ast_changed = True # Default to true so we run at least once
        while ast_changed:
            ast_changed = False
            for optimization in optimization_pass:
                changed, new_node = optimization.optimize(new_node, pred)
                ast_changed |= changed

        settings.log(2, lambda: f'Optimized node: {new_node}')

        return new_node

