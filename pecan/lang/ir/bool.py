#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

from pecan.automata.automaton import TrueAutomaton, FalseAutomaton

class Conjunction(BinaryIRPredicate):
    def __init__(self, a, b):
        super().__init__(a, b)

    def evaluate_node(self, prog):
        a_aut = self.a.evaluate(prog)

        if a_aut.is_empty():
            return a_aut

        b_aut = self.b.evaluate(prog)

        return a_aut & b_aut

    def transform(self, transformer):
        return transformer.transform_Conjunction(self)

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(BinaryIRPredicate):
    def __init__(self, a, b):
        super().__init__(a, b)

    def evaluate_node(self, prog):
        a_aut = self.a.evaluate(prog)
        b_aut = self.b.evaluate(prog)

        if a_aut.is_empty():
            return b_aut

        return a_aut | b_aut

    def transform(self, transformer):
        return transformer.transform_Disjunction(self)

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(UnaryIRPredicate):
    def __init__(self, a):
        super().__init__(a)

    def evaluate_node(self, prog):
        return self.a.evaluate(prog).complement()

    def transform(self, transformer):
        return transformer.transform_Complement(self)

    def __repr__(self):
        return '(¬{})'.format(self.a)

class FormulaTrue(IRPredicate):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        return TrueAutomaton()

    def transform(self, transformer):
        return transformer.transform_FormulaTrue(self)

    def __repr__(self):
        return '⊤'

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__

    def __hash__(self):
        return 0 # No fields to hash

class FormulaFalse(IRPredicate):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        return FalseAutomaton()

    def transform(self, transformer):
        return transformer.transform_FormulaFalse(self)

    def __repr__(self):
        return '⊥'

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__

    def __hash__(self):
        return 0 # No fields to hash

