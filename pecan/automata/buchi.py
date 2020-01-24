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

    def __init__(self, aut):
        super().__init__('buchi')
        self.aut = aut

    def conjunction(self, other):
        return BuchiAutomaton(spot.product(self.get_aut(), other.get_aut()))

    def disjunction(self, other):
        return BuchiAutomaton(spot.product_or(self.get_aut(), other.get_aut()))

    def complement(self):
        return BuchiAutomaton(spot.complement(self.get_aut()))

    def substitute(self, subs):
        return BuchiAutomaton(BuchiTransformer(self.postprocess(), Substitution(subs).substitute).transform())

    def project(self, var_refs):
        from pecan.lang.ir.prog import VarRef
        var_names = [v.var_name for v in var_refs if type(v) is VarRef]
        return BuchiAutomaton(BuchiProjection(self.postprocess(), var_names).project())

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

    def get_aut(self):
        # self.aut = spot.remove_alternation(self.postprocess())
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

class BuchiTransformer:
    def __init__(self, original_aut, formula_builder):
        self.original_aut = original_aut
        self.formula_builder = formula_builder

    def transform(self):
        # Build a new automata with different edges
        new_aut = spot.make_twa_graph()

        # Set the acceptance condition to be same as the input automata
        acc = self.original_aut.get_acceptance()
        new_aut.set_acceptance(acc.used_sets().max_set(), acc)
        new_aut.new_states(self.original_aut.num_states())
        new_aut.set_init_state(self.original_aut.get_init_state_number())

        for e in self.original_aut.edges():
            # Convert to a formula because formulas are nicer to work with than the bdd's
            formula = spot.bdd_to_formula(e.cond)
            new_formula = self.formula_builder(formula)
            cond = formula_to_bdd(new_aut, new_formula)
            # print('Adding edge', e.src, e.dst, '(', formula, ')', '(', new_formula, ')', e.acc)
            new_aut.new_edge(e.src, e.dst, cond, e.acc)

        return new_aut

class Substitution:
    def __init__(self, subs):
        self.subs = subs

    def substitute(self, formula):
        if formula._is(spot.op_ap):
            if formula.ap_name() in self.subs:
                return spot.formula(self.subs[formula.ap_name()])
            else:
                return formula
        else:
            return formula.map(self.substitute)

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

class BuchiProjection:
    def __init__(self, aut, var_names):
        super().__init__()
        self.aut = aut
        self.var_names = var_names

    def project(self):
        for var in self.var_names:
            def build_projection_formula(formula):
                if_0 = Substitution({var: spot.formula('0')}).substitute(formula)
                if_1 = Substitution({var: spot.formula('1')}).substitute(formula)

                # The new edge condition should be:
                # [0/y]cond | [1/y]cond
                # where cond is the original condition. That is, the edge is taken if it holds with y being false or y being true.
                return spot.formula_Or([if_0, if_1])
            self.aut = BuchiTransformer(self.aut, build_projection_formula).transform()
        return self.aut

