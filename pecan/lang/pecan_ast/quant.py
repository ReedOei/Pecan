#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import spot

from pecan.lang.pecan_ast.prog import *
from pecan.lang.pecan_ast.bool import *
from pecan.tools.automaton_tools import Projection

class Forall(Predicate):
    def __init__(self, var, pred):
        super().__init__()
        self.var = var
        self.pred = pred

    def evaluate_node(self, prog):
        return Complement(Exists(self.var, Complement(self.pred))).evaluate(prog)

    def __repr__(self):
        return '(∀{} ({}))'.format(self.var, self.pred)

class Exists(Predicate):
    def __init__(self, var, pred):
        super().__init__()
        self.var = var
        self.pred = pred

    def evaluate_node(self, prog):
        return Projection(self.pred.evaluate(prog), [self.var]).project()

    def __repr__(self):
        return '(∃{} ({}))'.format(self.var, self.pred)

