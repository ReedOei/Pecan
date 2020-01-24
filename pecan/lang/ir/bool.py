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

class BoolConst(IRPredicate):
    def __init__(self, bool_val):
        super().__init__()
        self.bool_val = bool_val

    def evaluate_node(self, prog):
        if self.bool_val:
            return TrueAutomaton()
        else:
            return FalseAutomaton()

    def transform(self, transformer):
        return transformer.transform_BoolConst(self)

    def __repr__(self):
        if self.bool_val:
            return '⊤'
        else:
            return '⊥'

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.bool_val == other.bool_val

    def __hash__(self):
        return hash(self.bool_val) # No fields to hash

