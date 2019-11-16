#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce
from itertools import chain # line 26

import buddy
import spot

class AutomatonTransformer:
    def __init__(self, original_aut, formula_builder, bdict = None, aps = None):
        self.original_aut = original_aut.postprocess('BA') # Ensure that the automata we get is a Buchi (possible nondeterministic) automata
        self.formula_builder = formula_builder
        self.bdict = bdict             # transform to use the given bdict
        self.aps = aps                 # tranform into exactly the given aps. Unrestrict aps if unspecified. TODO: Maybe check formula_builder that it shouldn't use other aps. 

    def transform(self):
        # Build a new automata with different edges
        bdict = spot.make_bdd_dict() if self.bdict is None else self.bdict
        new_aut = spot.make_twa_graph(bdict)

        aps = {}
        for ap in self.original_aut.ap() if self.aps is None else self.aps:
            aps[ap.ap_name()] = buddy.bdd_ithvar(new_aut.register_ap(ap.ap_name()))
        
        # old_aps_gen = (ap for ap in self.original_aut.ap() if ap not in self.delete_aps) 
        # new_aps_gen = (ap for ap in self.new_aps if ap not in self.delete_aps)
        

        new_aut.set_buchi() # Set the acceptance condition to the normal Buchi acceptance condition
        new_aut.new_states(self.original_aut.num_states())
        new_aut.set_init_state(0)

        for e in self.original_aut.edges():
            # Convert to a formula because formulas are nicer to work with than the bdd's
            formula = spot.formula(spot.bdd_format_formula(self.original_aut.get_dict(), e.cond))
            new_formula = self.formula_builder(formula)
            cond = self.create_edge_condition(new_aut, new_formula)
            # print('Adding edge', e.src, e.dst, '(', new_formula, ')', e.acc)
            new_aut.new_edge(e.src, e.dst, cond, e.acc)

        return new_aut

    def create_edge_condition(self, aut, new_formula):
        return FormulaToBdd(aut, new_formula).translate()


class AutomatonTransformer2:
    def __init__(self, original_aut, formula_builder):
        self.original_aut = original_aut.postprocess('BA') # Ensure that the automata we get is a Buchi (possible nondeterministic) automata
        self.formula_builder = formula_builder
        # self.bdict = bdict             # transform to use the given bdict
        # self.aps = aps                 # tranform into exactly the given aps. Unrestrict aps if unspecified. TODO: Maybe check formula_builder that it shouldn't use other aps. 

    def transform(self):
        # Build a new automata with different edges
        new_aut = spot.make_twa_graph()

        aps = {}
        for ap in self.original_aut.ap():
            aps[ap.ap_name()] = buddy.bdd_ithvar(new_aut.register_ap(ap.ap_name()))
        
        # old_aps_gen = (ap for ap in self.original_aut.ap() if ap not in self.delete_aps) 
        # new_aps_gen = (ap for ap in self.new_aps if ap not in self.delete_aps)
        

        new_aut.set_buchi() # Set the acceptance condition to the normal Buchi acceptance condition
        new_aut.new_states(self.original_aut.num_states())
        new_aut.set_init_state(0)

        for e in self.original_aut.edges():
            # Convert to a formula because formulas are nicer to work with than the bdd's
            formula = spot.formula(spot.bdd_format_formula(self.original_aut.get_dict(), e.cond))
            new_formula = self.formula_builder(formula)
            cond = self.create_edge_condition(new_aut, new_formula)
            # print('Adding edge', e.src, e.dst, '(', new_formula, ')', e.acc)
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

