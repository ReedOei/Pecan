#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import itertools as it

import buddy
import spot

from pecan.automata.automaton import Automaton, FalseAutomaton
from pecan.utility import VarMap
from pecan.settings import settings

import PySimpleAutomata.NFA as NFA

# import foma.foma.python.foma as foma

class FiniteAutomaton(Automaton):
    fresh_counter = 0
    @staticmethod
    def fresh_ap():
        label = f"var{FiniteAutomaton.fresh_counter}"
        FiniteAutomaton.fresh_counter += 1
        return label

    # This exists so that we ensure all names generated are fresh.
    # It gets called by the various methods that may create an automaton which already uses of the reserved __ap#N names
    # such as loading an automaton from a file.
    @staticmethod
    def update_counter(ap_name):
        if ap_name.startswith('var'):
            ap_num = int(ap_name.split('var')[1])
            FiniteAutomaton.id = max(FiniteAutomaton.id, ap_num) + 1

    @classmethod
    def as_finite(cls, aut):
        if aut.get_aut_type() == 'true':
            return cls.true_aut()
        elif aut.get_aut_type() == 'false':
            return cls.false_aut()
        else:
            raise NotImplementedError

    @classmethod
    def true_aut(cls):
        f = FiniteAutomaton({
                'alphabet': set(),
                'states': set(),
                'initial_states': set(),
                'accepting_states': set(),
                'transitions': {}
            }, {})
        f.special_attr = 'true'
        return f

    @classmethod
    def false_aut(cls):
        f = FiniteAutomaton({
                'alphabet': set(),
                'states': set(),
                'initial_states': set(),
                'accepting_states': set(),
                'transitions': {}
            }, {})
        f.special_attr = 'false'
        return f

    def __init__(self, aut, var_map):
        super().__init__('finite')

        # The internal automaton representation
        self.aut = aut

        # A map (V \to (N x Sigma)) mapping variables to their index in the symbol and the alphabet of the symbol
        self.var_map = var_map

        self.special_attr = None

    def get_var_map(self):
        return self.var_map

    def augment_vars(self, other):
        new_var_map = dict(self.var_map)
        cur_idx = len(new_var_map)

        for v, (idx, alphabet) in other.var_map.items():
            if v not in new_var_map:
                new_var_map[v] = (cur_idx, alphabet)
                cur_idx += 1

        new_l = self.with_var_map(new_var_map)
        new_r = other.with_var_map(new_var_map)

        return new_l, new_r, new_var_map

    def with_var_map(self, new_var_map):
        alphabets = list(range(len(new_var_map)))
        for v, (idx, alphabet) in new_var_map.items():
            alphabets[idx] = alphabet
        new_alphabet = set(','.join(syms) for syms in it.product(*alphabets))

        new_transitions = {}
        for (src, sym), dsts in self.aut['transitions'].items():
            new_syms = list(range(len(new_var_map)))

            # Copy over the old symbols
            syms = sym.split(',')
            for v, (idx, alphabet) in self.var_map.items():
                new_syms[new_var_map[v][0]] = [syms[idx]]

            for v, (idx, alphabet) in new_var_map.items():
                if not v in self.var_map:
                    new_syms[idx] = alphabet

            for new_sym in it.product(*new_syms):
                new_transitions[(src, ','.join(new_sym))] = dsts

        return {
            'alphabet': new_alphabet,
            'states': self.aut['states'],
            'initial_states': self.aut['initial_states'],
            'accepting_states': self.aut['accepting_states'],
            'transitions': new_transitions
        }

    def conjunction(self, other):
        if self.special_attr == 'true' or other.special_attr == 'false':
            return other
        elif self.special_attr == 'false' or other.special_attr == 'true':
            return self
        else:
            aut_l, aut_r, new_var_map = self.augment_vars(other)
            print(aut_l)
            print(aut_r)
            return FiniteAutomaton(NFA.nfa_intersection(aut_l, aut_r), new_var_map)

    def disjunction(self, other):
        aut_l = self.cross_prod(other)
        aut_r = other.cross_prod(self)

        return FiniteAutomaton(aut_l.aut & aut_r.aut, aut_l.var_map)

    def complement(self):
        return FiniteAutomaton(NFA.nfa_complementation(self.aut), self.var_map)

    def relabel(self):
        return self

    def substitute(self, arg_map, env_var_map):
        new_var_map = VarMap()
        ap_subs = {}

        for formal_arg, actual_arg in arg_map.items():
            # Get the aps for the formal argument in this automaton
            formal_aps = self.var_map[formal_arg]

            # Get the aps for the actual argument in the current environment
            actual_aps = env_var_map.get_or_gen(actual_arg, self.fresh_ap, len(formal_aps))

            # Set up the substitutions we need to do
            for formal_ap, actual_ap in zip(formal_aps, actual_aps):
                ap_subs[formal_ap] = actual_ap

            # Rename the formal arg to the actual arg, but leave the aps as the formal aps because that'll be done by `ap_substitute` below
            new_var_map[actual_arg] = formal_aps

        # print('substitute()', arg_map, new_var_map, env_var_map, ap_subs)

        return BuchiAutomaton(self.aut, new_var_map).ap_substitute(ap_subs)

    def project(self, var_refs, env_var_map):
        from pecan.lang.ir.prog import VarRef
        aps = []
        pecan_var_names = []

        for v in var_refs:
            if type(v) is VarRef:
                aps.extend(self.var_map[v.var_name])
                pecan_var_names.append(v.var_name)

        result = self.ap_project(aps)

        for var_name in pecan_var_names:
            # It may not be there (e.g., it's perfectly valid to do "exists x. y = y", even if it's pointless)
            if var_name in result.get_var_map():
                result.get_var_map().pop(var_name)

            if var_name in env_var_map:
                env_var_map.pop(var_name)

        return result

    def is_empty(self):
        return not NFA.nfa_nonemptiness_check(self.aut)

    def truth_value(self):
        if self.is_empty(): # If we accept nothing, we are false
            return 'false'
        elif self.complement().is_empty(): # If our complement accepts nothing, we accept everything, so we are true
            return 'true'
        else: # Otherwise, we are neither true nor false: i.e., not all variables have been eliminated
            return 'sometimes'

    def num_states(self):
        return len(self.aut['states'])

    def num_edges(self):
        return len(self.aut['transitions'])

    # Should return a string of SVG data
    def show(self):
        return str(self.aut)

    def get_aut(self):
        return self.aut

    def to_str(self):
        return '{}'.format({'var_map': self.var_map, 'aut': self.aut})

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.to_str())

def buchi_transform(original_aut, builder):
    # Build a new automata with different edges
    new_aut = spot.make_twa_graph()

    # Set the acceptance condition to be same as the input automata
    acc = original_aut.get_acceptance()
    new_aut.set_acceptance(acc.used_sets().max_set(), acc)
    new_aut.new_states(original_aut.num_states())
    new_aut.set_init_state(original_aut.get_init_state_number())

    builder.pre_build(new_aut)

    ne = original_aut.num_edges()

    if settings.get_debug_level() > 1:
        import sys

        for i, e in enumerate(original_aut.edges()):
            cond = builder.build_cond(e.cond)
            new_aut.new_edge(e.src, e.dst, cond, e.acc)

            if i % 10000 == 0:
                sys.stdout.write('\r{} of {} edges ({:.2f}%)'.format(i, ne, 100 * i / ne))

        print()
    else:
        # TODO: This does the same thing as above, but it just doesn't run the check/print every time.
        #       We could run the same loop and check for debug every time, but this minor overhead
        #       accumulates a fair bit once you get to having millions of edges, so we duplicate it.
        #       It would still be nice to avoid this, though.
        for e in original_aut.edges():
            cond = builder.build_cond(e.cond)
            new_aut.new_edge(e.src, e.dst, cond, e.acc)

    builder.post_build(new_aut)

    return new_aut

class Builder:
    def pre_build(self, new_aut):
        pass

    def post_build(self, new_aut):
        pass

    def build_cond(self, cond):
        return cond

class Substitution(Builder):
    def __init__(self, subs):
        self.subs = subs

    def pre_build(self, new_aut):
        for k, v in self.subs.items():
            if type(v) is str:
                self.subs[k] = buddy.bdd_ithvar(new_aut.register_ap(v))

    def build_cond(self, cond):
        # TODO: ideally we could use the bdd_veccompose to do them all at once instead of
        #   one at a time, but spot doesn't expose the bdd_newpair function to python at the moment...
        for var, new_formula in self.subs.items():
            # old = cond
            cond = buddy.bdd_compose(cond, new_formula, var)
            # print('after ({} |-> {}), is now {}, was {}'.format(spot.bdd_to_formula(buddy.bdd_ithvar(var)), spot.bdd_to_formula(new_formula), spot.bdd_to_formula(cond), spot.bdd_to_formula(old)))

        return cond

