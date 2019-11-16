#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import spot

from pecan.lang.pecan_ast.prog import *
from pecan.lang.pecan_ast.bool import *
from pecan.tools.automaton_tools import Projection

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
        return Projection(self.pred.evaluate(prog), [self.var_name]).project()

    def __repr__(self):
        return '(∃{} ({}))'.format(self.var_name, self.pred)

