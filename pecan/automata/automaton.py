#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

class Automaton:
    def __init__(self, aut_type_name):
        self.aut_type_name = aut_type_name

    def get_aut_type(self):
        return self.aut_type_name

    # -------------------------------------------------------
    # Interface methods (should be implemented for all subclasses):
    # -------------------------------------------------------

    # To implement an automaton, we only need implement either conjunction or disjunction, and complement
    # In practice, it will probably be more efficient to implement all three
    def conjunction(self, other):
        return self.complement(self.disjunction(self.complement(self), self.complement(other)))

    def disjunction(self, other):
        return self.complement(self.conjunction(self.complement(self), self.complement(other)))

    def complement(self):
        raise NotImplementedError

    def substitute(self, subs, env_var_map):
        raise NotImplementedError

    def project(self, var_refs, env_var_map):
        raise NotImplementedError

    def is_empty(self):
        raise NotImplementedError

    def truth_value(self):
        raise NotImplementedError

    def num_states(self):
        raise NotImplementedError

    def num_edges(self):
        raise NotImplementedError

    def accepting_word(self):
        raise NotImplementedError

    def to_str(self):
        raise NotImplementedError

    # Should return a string of SVG data
    def show(self):
        raise NotImplementedError

    def save(self, filename):
        raise NotImplementedError

    # -------------------------------------------------------------------
    # Optional methods (e.g., for simplification, minimization, etc):
    # -------------------------------------------------------------------
    def simplify_edges(self):
        return self

    def simplify_states(self):
        return self

    def merge_edges(self):
        return self

    def merge_states(self):
        return self

    # Allows conversion between types of automata, if desired
    def custom_convert(self, other):
        raise NotImplementedError

    def shuffle(self, is_disj, other):
        raise NotImplementedError

    def relabel(self):
        return self

    def simplify(self):
        return self

    # -------------------------------------------------------
    # Default implementations:
    # -------------------------------------------------------
    def __and__(self, other):
        return self.conjunction(self.convert(other))

    def __or__(self, other):
        return self.disjunction(self.convert(other))

    def contains(self, other):
        return (self.complement() | other).truth_value() == 'true'

    def convert(self, other):
        if self.get_aut_type() == other.get_aut_type():
            return other
        else:
            return self.custom_convert(other)

class TrueAutomaton(Automaton):
    def __init__(self):
        super().__init__('true')

    def conjunction(self, other):
        return other

    def disjunction(self, other):
        return self

    def complement(self):
        return FalseAutomaton()

    def substitute(self, arg_map, env_var_map):
        return self

    def project(self, var_refs, env_var_map):
        return self

    def is_empty(self):
        return False

    def truth_value(self):
        return 'true'

    def num_states(self):
        return -1

    def num_edges(self):
        return -1

    def custom_convert(self, other):
        return other

    def to_str(self):
        return str(self)

class FalseAutomaton(Automaton):
    def __init__(self):
        super().__init__('false')

    # We switch order so that we get converted into the proper automata type
    def conjunction(self, other):
        return self

    def disjunction(self, other):
        return other

    def complement(self):
        return TrueAutomaton()

    def substitute(self, arg_map, env_var_map):
        return self

    def project(self, var_refs, env_var_map):
        return self

    def is_empty(self):
        return True

    def truth_value(self):
        return 'false'

    def num_states(self):
        return -1

    def num_edges(self):
        return -1

    def custom_convert(self, other):
        return other

    def to_str(self):
        return str(self)

