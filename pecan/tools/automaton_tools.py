#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce
import itertools as it

import buddy
import spot

class AutomatonTransformer:
    def __init__(self, original_aut, formula_builder):
        self.original_aut = original_aut.postprocess('BA', 'small') # Ensure that the automata we get is a Buchi (possible nondeterministic) automata
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
            cond = self.create_edge_condition(new_aut, new_formula)
            # print('Adding edge', e.src, e.dst, '(', formula, ')', '(', new_formula, ')', e.acc)
            new_aut.new_edge(e.src, e.dst, cond, e.acc)

        return new_aut

    def create_edge_condition(self, aut, new_formula):
        return formula_to_bdd(aut, new_formula)

class Substitution:
    def __init__(self, subs):
        self.subs = subs

    def substitute(self, formula):
        if formula._is(spot.op_ap):
            return self.subs.get(formula.ap_name(), formula)
        else:
            return formula.map(self.substitute)

def build_bdd(kind, children):
    if kind == spot.op_And:
        return reduce(lambda a, b: a & b, children)
    elif kind == spot.op_Or:
        return reduce(lambda a, b: a | b, children)
    elif kind == spot.op_Not:
        return buddy.bdd_not(children[0])  # TODO: Put error check in here
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

class Projection:
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
            self.aut = AutomatonTransformer(self.aut, build_projection_formula).transform()
        return self.aut

class TruthValue:
    def __init__(self, pred):
        self.pred = pred

    def truth_value(self, prog):
        evaluated = self.pred.evaluate(prog)
        if evaluated.is_empty(): # If we accept nothing, we are false
            return 'false'
        elif spot.complement(evaluated).is_empty(): # If our complement accepts nothing, we accept everything, so we are true
            return 'true'
        else: # Otherwise, we are neither true nor false: i.e., not all variables have been eliminated
            return 'sometimes'

