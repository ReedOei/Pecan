#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.pecan_ast import *

class Conjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return spot.product(self.a.evaluate(prog), self.b.evaluate(prog))

    def transform(self, transformer):
        return transformer.transform_Conjunction(self)

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return spot.product_or(self.a.evaluate(prog), self.b.evaluate(prog))

    def transform(self, transformer):
        return transformer.transform_Disjunction(self)

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(Predicate):
    def __init__(self, a, use_not_equals=True):
        super().__init__()
        self.a = a
        self.use_not_equals = use_not_equals

    def evaluate_node(self, prog):
        # from pecan.lang.pecan_ast.arith import Equals, NotEquals
        # if self.use_not_equals and type(self.a) is Equals:
        #     return NotEquals(self.a.a, self.a.b).evaluate(prog)
        # else:
        return spot.complement(self.a.evaluate(prog))

    def transform(self, transformer):
        return transformer.transform_Complement(self)

    def __repr__(self):
        return '(¬{})'.format(self.a)

class Iff(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return Conjunction(Implies(self.a, self.b), Implies(self.b, self.a)).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Iff(self)

    def __repr__(self):
        return '({} ⟺  {})'.format(self.a, self.b)

class Implies(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        return Disjunction(Complement(self.a), self.b).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Implies(self)

    def __repr__(self):
        return '({} ⟹  {})'.format(self.a, self.b)

class FormulaTrue(Predicate):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        return spot.translate("1")

    def transform(self, transformer):
        return transformer.transform_FormulaTrue(self)

    def __repr__(self):
        return '⊤'

class FormulaFalse(Predicate):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        return spot.translate("0")

    def transform(self, transformer):
        return transformer.transform_FormulaFalse(self)

    def __repr__(self):
        return '⊥'

