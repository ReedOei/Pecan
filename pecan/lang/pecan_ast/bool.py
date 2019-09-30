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
        return Iff(self.a, self.b).evaluate(prog)

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Iff(Complement(self.a), self.b).evaluate(prog)

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

class Conjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return spot.product(self.a.evaluate(prog), self.b.evaluate(prog))

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return spot.product_or(self.a.evaluate(prog), self.b.evaluate(prog))

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(Predicate):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def evaluate(self, prog):
        return spot.complement(self.a.evaluate(prog))

    def __repr__(self):
        return '(¬{})'.format(self.a, self.b)

class Iff(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Conjunction(Implies(self.a, self.b), Implies(self.b, self.a)).evaluate(prog)

    def __repr__(self):
        return '({} ⟺  {})'.format(self.a, self.b)

class Implies(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Disjunction(Complement(self.a), self.b).evaluate(prog)

    def __repr__(self):
        return '({} ⟹  {})'.format(self.a, self.b)

