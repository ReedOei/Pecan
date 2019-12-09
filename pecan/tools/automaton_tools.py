#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

import buddy
import spot

class AutomatonTransformer:
    def __init__(self, original_aut, formula_builder):
        self.original_aut = original_aut.postprocess('BA', 'small') # Ensure that the automata we get is a Buchi (possible nondeterministic) automata
        self.formula_builder = formula_builder

    def transform(self):
        # Build a new automata with different edges
        new_aut = spot.make_twa_graph()

        aps = {}
        for ap in self.original_aut.ap():
            aps[ap.ap_name()] = buddy.bdd_ithvar(new_aut.register_ap(ap.ap_name()))

        # new_aut.set_buchi() # Set the acceptance condition to the normal Buchi acceptance condition

        # Set the acceptance condition to be same as the input automata
        acc = self.original_aut.get_acceptance()
        new_aut.set_acceptance(acc.used_sets().max_set(), acc)
        new_aut.new_states(self.original_aut.num_states())
        new_aut.set_init_state(self.original_aut.get_init_state_number())

        for e in self.original_aut.edges():
            # Convert to a formula because formulas are nicer to work with than the bdd's
            formula = spot.formula(spot.bdd_format_formula(self.original_aut.get_dict(), e.cond))
            new_formula = self.formula_builder(formula)
            cond = self.create_edge_condition(new_aut, new_formula)
            # print('Adding edge', e.src, e.dst, '(', formula, ')', '(', new_formula, ')', e.acc)
            new_aut.new_edge(e.src, e.dst, cond, e.acc)

        return new_aut

    def create_edge_condition(self, aut, new_formula):
        return FormulaToBdd(aut, new_formula).translate()

class Substitution:
    def __init__(self, subs):
        self.subs = subs

    def substitute(self, formula):
        if formula._is(spot.op_ap):
            if formula.ap_name() in self.subs:
                return self.subs[formula.ap_name()]
            else:
                return formula
        else:
            return formula.map(self.substitute)

class FormulaToBdd:
    def __init__(self, aut, formula):
        self.aut = aut
        self.formula = formula

    def translate(self):
        return self.run_translation(self.formula)

    def build_bdd(self, kind, children):
        if kind == spot.op_And:
            return reduce(lambda a, b: a & b, children)
        elif kind == spot.op_Or:
            return reduce(lambda a, b: a | b, children)
        elif kind == spot.op_Not:
            return buddy.bdd_not(children[0]) # TODO: Put error check in here
        elif kind == spot.op_tt:
            return buddy.bddtrue
        elif kind == spot.op_ff:
            return buddy.bddfalse
        else:
            raise Exception('Unhandled formula kind: {}'.format(kind))

    def run_translation(self, formula):
        if formula._is(spot.op_ap): # op_ap is 'atomic proposition' (i.e., variable)
            return buddy.bdd_ithvar(self.aut.register_ap(formula.ap_name()))
        else:
            new_children = []
            for i in range(formula.size()):
                new_child = self.run_translation(formula[i])

                if new_child is not None:
                    new_children.append(new_child)

            return self.build_bdd(formula.kind(), new_children)

class Projection:
    def __init__(self, aut, var_names):
        super().__init__()
        self.aut = aut
        self.var_names = var_names

    def project(self):
        # An alternate version that projects all the variables at once. Doesn't really seem to be any more efficient
        # def build_projection_formula(formula):
        #     conds = []
        #     for vals in it.product([0,1], repeat=len(self.var_names)):
        #         conds.append(Substitution({var: spot.formula(str(val)) for var, val in zip(self.var_names, vals)}).substitute(formula))

        #     # The new edge condition should be:
        #     # [0/y]cond | [1/y]cond
        #     # where cond is the original condition. That is, the edge is taken if it holds with y being false or y being true.
        #     return spot.formula_Or(conds)
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

