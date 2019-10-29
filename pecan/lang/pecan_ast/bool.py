#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.pecan_ast.prog import *

class Equals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        eq_aut = spot.formula('G(({0} -> {1}) & ({1} -> {0}))'.format(val_a, val_b)).translate()
        return self.show_if_debug(prog, spot.product(eq_aut, spot.product(aut_a, aut_b)))

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return self.show_if_debug(prog, Complement(Equals(self.a, self.b)).evaluate(prog))

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

class Conjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return self.show_if_debug(prog, spot.product(self.a.evaluate(prog), self.b.evaluate(prog)))

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return self.show_if_debug(prog, spot.product_or(self.a.evaluate(prog), self.b.evaluate(prog)))

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(Predicate):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def evaluate(self, prog):
        return self.show_if_debug(prog, spot.complement(self.a.evaluate(prog)))

    def __repr__(self):
        return '(¬{})'.format(self.a)

class Iff(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return self.show_if_debug(prog, Conjunction(Implies(self.a, self.b), Implies(self.b, self.a)).evaluate(prog))

    def __repr__(self):
        return '({} ⟺  {})'.format(self.a, self.b)

class Implies(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return self.show_if_debug(prog, Disjunction(Complement(self.a), self.b).evaluate(prog))

    def __repr__(self):
        return '({} ⟹  {})'.format(self.a, self.b)

