#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast import *

class Conjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_Conjunction(self)

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_Disjunction(self)

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(Predicate):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def transform(self, transformer):
        return transformer.transform_Complement(self)

    def __repr__(self):
        return '(¬{})'.format(self.a)

class Iff(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_Iff(self)

    def __repr__(self):
        return '({} ⟺  {})'.format(self.a, self.b)

class Implies(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_Implies(self)

    def __repr__(self):
        return '({} ⟹  {})'.format(self.a, self.b)

class FormulaTrue(Predicate):
    def __init__(self):
        super().__init__()

    def transform(self, transformer):
        return transformer.transform_FormulaTrue(self)

    def __repr__(self):
        return '⊤'

class FormulaFalse(Predicate):
    def __init__(self):
        super().__init__()

    def transform(self, transformer):
        return transformer.transform_FormulaFalse(self)

    def __repr__(self):
        return '⊥'

