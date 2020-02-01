#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import copy
from functools import reduce

import buddy
import spot

from pecan.automata.automaton import Automaton

def merge(aut, var_map, other_var_map):
    merged_var_map = copy.deepcopy(var_map)
    subs = {}

    for var, aps in other_var_map.items():
        if var in merged_var_map:
            merged_aps = merged_var_map[var]

            if len(merged_aps) != len(aps):
                raise Exception('Cannot merge {}: representations differ in length ({}, {})'.format(var, merged_aps, aps))

            for a, b in zip(merged_aps, aps):
                subs[b] = a
        else:
            merged_var_map[var] = aps

    # print('merge()', var_map, other_var_map, merged_var_map, subs)

    return BuchiAutomaton(aut, merged_var_map).ap_substitute(subs)

def clean_subs(subs):
    to_pop = []

    for k, v in subs.items():
        if k == v:
            to_pop.append(k)

    for k in to_pop:
        subs.pop(k)

class BuchiAutomaton(Automaton):
    id = 0
    @staticmethod
    def fresh_ap():
        label = f"__ap{BuchiAutomaton.id}"
        BuchiAutomaton.id += 1
        return label

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

    def __init__(self, aut, var_map):
        super().__init__('buchi')

        # The interal automaton representation
        self.aut = aut

        # Maps pecan variables to internal variables
        self.var_map = var_map

    def get_var_map(self):
        return self.var_map

    def combine_var_map(self, other):
        new_var_map = copy.deepcopy(self.get_var_map())

        for var_name in self.get_var_map():
            if var_name in other.get_var_map():
                if self.get_var_map()[var_name] != other.get_var_map()[var_name]:
                    raise Exception('Underlying representation of variable {} does not match ({}, {})'.format(var_name, self.get_var_map(), other.get_var_map()))

        new_var_map.update(other.get_var_map())
        return new_var_map

    def conjunction(self, other):
        return merge(spot.product(self.get_aut(), other.get_aut()), self.get_var_map(), other.get_var_map())

    def disjunction(self, other):
        return merge(spot.product_or(self.get_aut(), other.get_aut()), self.get_var_map(), other.get_var_map())

    def complement(self):
        return BuchiAutomaton(spot.complement(self.get_aut()), self.var_map)

    def call(self, arg_map):
        # Generate fresh aps for all the aps in this automaton
        new_var_map = {}
        ap_subs = {}
        subs = {}

        for v, old_aps in self.get_var_map().items():
            aps = []

            for ap in old_aps:
                new_ap = self.fresh_ap()
                subs[ap] = new_ap
                aps.append(new_ap)

            if v in arg_map:
                if arg_map[v] in new_var_map:
                    final_aps = new_var_map[arg_map[v]]

                    for final, temp in zip(final_aps, aps):
                        ap_subs[temp] = final
                else:
                    new_var_map[arg_map[v]] = aps
            else:
                new_var_map[v] = aps

        for orig_ap in subs:
            while subs[orig_ap] in ap_subs:
                subs[orig_ap] = ap_subs[subs[orig_ap]]

        # print('call()', self.get_var_map(), subs, new_var_map, subs)

        return BuchiAutomaton(self.get_aut(), new_var_map).ap_substitute(subs)

    def substitute(self, subs):
        new_var_map = {}
        ap_subs = {}

        for v, aps in self.get_var_map().items():
            if v in subs:
                if subs[v] in new_var_map:
                    final_aps = new_var_map[subs[v]]

                    for final, temp in zip(final_aps, aps):
                        ap_subs[temp] = final
                else:
                    new_var_map[subs[v]] = aps
            else:
                new_var_map[v] = aps

        # print('substitute()', self.get_var_map(), subs, new_var_map, ap_subs)

        return BuchiAutomaton(self.get_aut(), new_var_map).ap_substitute(ap_subs)

    def ap_substitute(self, subs):
        clean_subs(subs)

        if len(subs) == 0:
            return self

        return BuchiTransformer(self, Substitution(subs)).transform()

    def project(self, var_refs):
        from pecan.lang.ir.prog import VarRef
        var_names = []
        pecan_var_names = []

        for v in var_refs:
            if type(v) is VarRef:
                var_names.extend(self.var_map[v.var_name])
                pecan_var_names.append(v.var_name)

        result = self
        for var_name in var_names:
            result = BuchiTransformer(result.postprocess(), BuchiProjection(var_name)).transform()

        for var_name in pecan_var_names:
            # It may not be there (e.g., it's perfectly valid to do "exists x. y = y", even if it's pointless)
            if var_name in result.get_var_map():
                result.get_var_map().pop(var_name)

        return result

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
        return self.postprocess().aut.show()

    def get_aut(self):
        return self.aut

    def merge_edges(self):
        self.get_aut().merge_edges()
        return self

    def merge_states(self):
        self.get_aut().merge_states()
        return self

    def accepting_word(self):
        acc_word = self.postprocess().get_aut().accepting_word()

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
            return BuchiAutomaton(spot.translate('1'), {})
        elif other.get_aut_type() == 'false':
            return BuchiAutomaton(spot.translate('0'), {})
        else:
            raise NotImplementedError

    def postprocess(self):
        if not self.aut.is_sba():
            self.aut = self.aut.postprocess('BA') # Ensure that the automata we have is a Buchi (possible nondeterministic) automata
        return self

    def shuffle(self, is_disj, other):
        new_var_map = self.combine_var_map(other)
        return BuchiAutomaton(ShuffleAutomata(a_aut.get_aut(), b_aut.get_aut()).shuffle(self.disjunction), new_var_map)

def build_bdd(kind, children):
    if kind == spot.op_And:
        return reduce(lambda a, b: a & b, children)
    elif kind == spot.op_Or:
        return reduce(lambda a, b: a | b, children)
    elif kind == spot.op_Not:
        return buddy.bdd_not(children[0])
    elif kind == spot.op_tt:
        return buddy.bddtrue
    elif kind == spot.op_ff:
        return buddy.bddfalse
    else:
        raise Exception('Unhandled formula kind: {}'.format(kind))

def formula_to_bdd(aut, formula):
    if formula._is(spot.op_ap): # op_ap is 'atomic proposition' (i.e., variable)
        return buddy.bdd_ithvar(aut.register_ap(formula.ap_name()))
    else:
        new_children = []
        for i in range(formula.size()):
            new_child = formula_to_bdd(aut, formula[i])

            if new_child is not None:
                new_children.append(new_child)

        return build_bdd(formula.kind(), new_children)

class BuchiTransformer:
    def __init__(self, original_aut, builder):
        self.original_aut = original_aut
        self.builder = builder

    def transform(self):
        # Build a new automata with different edges
        new_aut = spot.make_twa_graph()

        inner_aut = self.original_aut.get_aut()

        # Set the acceptance condition to be same as the input automata
        acc = inner_aut.get_acceptance()
        new_aut.set_acceptance(acc.used_sets().max_set(), acc)
        new_aut.new_states(inner_aut.num_states())
        new_aut.set_init_state(inner_aut.get_init_state_number())

        for e in inner_aut.edges():
            # Convert to a formula because formulas are nicer to work with than the bdd's
            formula = spot.bdd_to_formula(e.cond)
            new_formula = self.builder.transform_formula(formula)
            cond = spot.formula_to_bdd(new_formula, new_aut.get_dict(), new_aut)
            # print('Adding edge', e.src, e.dst, '(', formula, ')', '(', new_formula, ')', e.acc)
            new_aut.new_edge(e.src, e.dst, cond, e.acc)

        return BuchiAutomaton(new_aut, self.builder.transform_var_map(self.original_aut.get_var_map()))

class Builder:
    def transform_formula(self, formula):
        return formula

    def transform_var_map(self, var_map):
        return copy.deepcopy(var_map)

class Substitution(Builder):
    def __init__(self, subs):
        self.subs = subs

    def transform_formula(self, formula):
        if formula._is(spot.op_ap):
            if formula.ap_name() in self.subs:
                return spot.formula(self.subs[formula.ap_name()])
            else:
                return formula
        else:
            return formula.map(self.transform_formula)

    def transform_var_map(self, var_map):
        new_var_map = {}

        for v, aps in var_map.items():
            new_var_map[v] = [self.subs.get(ap, ap) for ap in aps]

        return new_var_map

class BuchiProjection(Builder):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def transform_formula(self, formula):
        if_0 = Substitution({self.var_name: spot.formula('0')}).transform_formula(formula)
        if_1 = Substitution({self.var_name: spot.formula('1')}).transform_formula(formula)

        # The new edge condition should be:
        # [0/y]cond | [1/y]cond
        # where cond is the original condition. That is, the edge is taken if it holds with y being false or y being true.
        return spot.formula_Or([if_0, if_1])

