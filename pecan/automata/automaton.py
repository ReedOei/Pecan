#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

# To implement an automaton, we only need implement either conjunction or disjunction, and complement
# In practice, it will probably be more efficient to implement all three
class Automaton:
    def conjunction(self, other):
        return self.complement(self.disjunction(self.complement(self), self.complement(other)))

    def disjunction(self, other):
        return self.complement(self.conjunction(self.complement(self), self.complement(other)))

    def complement(self, other):
        raise NotImplementedError

    def substitute(self, subs):
        raise NotImplementedError

