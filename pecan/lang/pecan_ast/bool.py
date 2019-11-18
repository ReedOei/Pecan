#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.pecan_ast.prog import *
from pecan.tools.automaton_tools import Projection

class Equals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        eq_aut = spot.formula('G(({0} -> {1}) & ({1} -> {0}))'.format(val_a, val_b)).translate()
        result = spot.product(eq_aut, spot.product(aut_a, aut_b))
        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return result

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return Complement(Equals(self.a, self.b)).evaluate(prog)

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

class Conjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return spot.product(self.a.evaluate(prog), self.b.evaluate(prog))

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return spot.product_or(self.a.evaluate(prog), self.b.evaluate(prog))

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(Predicate):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def evaluate_node(self, prog):
        return spot.complement(self.a.evaluate(prog))

    def __repr__(self):
        return '(¬{})'.format(self.a)

class Iff(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return Conjunction(Implies(self.a, self.b), Implies(self.b, self.a)).evaluate(prog)

    def __repr__(self):
        return '({} ⟺  {})'.format(self.a, self.b)

class Implies(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return Disjunction(Complement(self.a), self.b).evaluate(prog)

    def __repr__(self):
        return '({} ⟹  {})'.format(self.a, self.b)

class FormulaTrue(Predicate):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        return spot.translate("1")

    def __repr__(self):
        return '⊤'

class FormulaFalse(Predicate):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        return spot.translate("0")

    def __repr__(self):
        return '⊥'

