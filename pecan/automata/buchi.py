#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

import buddy
import spot

from pecan.automata.automaton import Automaton

class BuchiAutomaton(Automaton):
    @staticmethod
    def as_buchi(aut):
        if aut.get_aut_type() == 'buchi':
            return aut
        elif aut.get_aut_type() == 'true':
            return BuchiAutomaton(spot.translate('1'))
        elif aut.get_aut_type() == 'false':
            return BuchiAutomaton(spot.translate('0'))
        else:
            raise NotImplementedError

    id = 0
    def fresh_ap(self):
        name = f'__ap{BuchiAutomaton.id}'
        BuchiAutomaton.id += 1
        return name

    def __init__(self, aut):
        super().__init__('buchi')
        self.aut = aut

    def conjunction(self, other):
        return BuchiAutomaton(spot.product(self.get_aut(), other.get_aut()))

    def disjunction(self, other):
        return BuchiAutomaton(spot.product_or(self.get_aut(), other.get_aut()))

    def complement(self):
        return BuchiAutomaton(spot.complement(self.get_aut()))

    def relabel(self, arguments=None):
        new_aps = {}
        for ap in self.aut.ap():
            new_aps[ap.ap_name()] = self.fresh_ap()

        for ap in arguments or []:
            new_aps[ap] = self.fresh_ap()

        return new_aps, self.substitute(new_aps)

    def substitute(self, subs):
        self.postprocess()

        bdd_subs = {}
        for k,v in subs.items():
            # If we try something like [x/x]P, just don't do anything
            if k == v:
                continue

            kvar = self.aut.register_ap(k)
            bdd_subs[kvar] = v

        if not bdd_subs:
            return self

        return BuchiAutomaton(buchi_transform(self.aut, Substitution(bdd_subs)))

    def project(self, var_refs):
        from pecan.lang.ir.prog import VarRef
        var_names = [v.var_name for v in var_refs if type(v) is VarRef]

        res_aut = self.aut.postprocess('BA')
        for var_name in var_names:
            if not res_aut.is_sba():
                res_aut = res_aut.postprocess('BA')

            res_aut = buchi_transform(res_aut, BuchiProjection(res_aut, var_name))

        return BuchiAutomaton(res_aut)

    def is_empty(self):
        return self.aut.is_empty()

    def truth_value(self):
        if self.aut.is_empty(): # If we accept nothing, we are false
            return 'false'
        elif spot.complement(self.aut).is_empty(): # If our complement accepts nothing, we accept everything, so we are true
            return 'true'
        else: # Otherwise, we are neither true nor false: i.e., not all variables have been eliminated
            return 'sometimes'

    def num_states(self):
        return self.aut.num_states()

    def num_edges(self):
        return self.aut.num_edges()

    # Should return a string of SVG data
    def show(self):
        return self.postprocess().show()

    def get_aut(self):
        return self.aut

    def merge_edges(self):
        self.get_aut().merge_edges()
        return self

    def merge_states(self):
        self.get_aut().merge_states()
        return self

    def accepting_word(self):
        acc_word = self.get_aut().accepting_word()

        if acc_word is None:
            return None

        acc_word.simplify()

        var_vals = {}
        var_names = []
        for formula in list(acc_word.prefix) + list(acc_word.cycle):
            for f in spot.atomic_prop_collect(spot.bdd_to_formula(formula)):
                var_names.append(f.ap_name())

        var_names = sorted(list(set(var_names)))
        prefixes = self.to_binary(var_names, acc_word.prefix)
        cycles = self.to_binary(var_names, acc_word.cycle)

        result = {}
        for var_name in var_names:
            result[var_name] = (prefixes[var_name], cycles[var_name])
        return result

    def to_binary(self, var_names, bdd_list):
        var_vals = {k: [] for k in var_names}

        for bdd in bdd_list[::-1]:
            formula = spot.bdd_to_formula(bdd)

            next_vals = {}
            self.process_formula(next_vals, formula)

            # If we didn't find a value for a variable in this part of the formula, that means it can be either True or False.
            # We arbitrarily choose False.
            for var_name in var_names:
                var_vals[var_name].insert(0, next_vals.get(var_name, False))

        return var_vals

    def process_formula(self, next_vals, formula):
        if formula._is(spot.op_ap):
            next_vals[formula.ap_name()] = True
        elif formula._is(spot.op_Not):
            next_vals[formula[0].ap_name()] = False
        elif formula._is(spot.op_And):
            for i in range(formula.size()):
                self.process_formula(next_vals, formula[i])
        elif formula._is(spot.op_tt):
            pass
        else:
            raise Exception('Cannot process formula: {}'.format(formula))

    def custom_convert(self, other):
        if other.get_aut_type() == 'true':
            return BuchiAutomaton(spot.translate('1'))
        elif other.get_aut_type() == 'false':
            return BuchiAutomaton(spot.translate('0'))
        else:
            raise NotImplementedError

    def postprocess(self):
        if not self.aut.is_sba():
            self.aut = self.aut.postprocess('BA') # Ensure that the automata we have is a Buchi (possible nondeterministic) automata
        return self.aut

    def save(self, filename):
        self.aut.save(filename)

    def to_str(self):
        return self.aut.to_str('hoa')

def buchi_transform(original_aut, builder):
    # Build a new automata with different edges
    new_aut = spot.make_twa_graph()

    # Set the acceptance condition to be same as the input automata
    acc = original_aut.get_acceptance()
    new_aut.set_acceptance(acc.used_sets().max_set(), acc)
    new_aut.new_states(original_aut.num_states())
    new_aut.set_init_state(original_aut.get_init_state_number())

    builder.pre_build(new_aut)

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

class BuchiProjection(Builder):
    def __init__(self, aut, var_name):
        super().__init__()
        self.aut = aut
        self.var_name = var_name
        self.bdd_var = self.aut.register_ap(var_name)

    def pre_build(self, new_aut):
        for ap in self.aut.ap():
            if ap.ap_name() != self.var_name:
                new_aut.register_ap(ap)

    def build_cond(self, cond):
        if_0 = Substitution({self.bdd_var: buddy.bddfalse}).build_cond(cond)
        if_1 = Substitution({self.bdd_var: buddy.bddtrue}).build_cond(cond)

        # The new edge condition should be:
        # [F/y]cond | [T/y]cond
        # where cond is the original condition. That is, the edge is taken if it holds with y being false or y being true.
        return if_0 | if_1
