#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import spot

from pecan.lang.pecan_ast.prog import *
from pecan.lang.pecan_ast.bool import *
from pecan.tools.automaton_tools import Substitution, AutomatonTransformer

class Forall(Predicate):
    def __init__(self, var_name, pred):
        super().__init__()
        self.var_name = var_name
        self.pred = pred

    def evaluate_node(self, prog):
        return Complement(Exists(self.var_name, Complement(self.pred))).evaluate(prog)

    def __repr__(self):
        return '(∀{} ({}))'.format(self.var_name, self.pred)

class Exists(Predicate):
    def __init__(self, var_name, pred):
        super().__init__()
        self.var_name = var_name
        self.pred = pred

    def evaluate_node(self, prog):
        evaluated = self.pred.evaluate(prog)
        return AutomatonTransformer(evaluated, self.build_exist_formula).transform()

    def build_exist_formula(self, formula):
        if_0 = Substitution({self.var_name: spot.formula('0')}).substitute(formula)
        if_1 = Substitution({self.var_name: spot.formula('1')}).substitute(formula)

        # The new edge condition should be:
        # [0/y]cond | [1/y]cond
        # where cond is the original condition. That is, the edge is taken if it holds with y being false or y being true.
        return spot.formula_Or([if_0, if_1])

    def __repr__(self):
        return '(∃{} ({}))'.format(self.var_name, self.pred)
