#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import spot

from functools import reduce

from pecan.lang.pecan_ast.prog import *
from pecan.lang.pecan_ast.bool import *

class Forall(Predicate):
    def __init__(self, var_name, pred):
        super().__init__()
        self.var_name = var_name
        self.pred = pred

    def evaluate(self, prog):
        return Complement(Exists(self.var_name, Complement(self.pred))).evaluate(prog)

    def __repr__(self):
        return '(∀{} ({}))'.format(self.var_name, self.pred)

class Exists(Predicate):
    def __init__(self, var_name, pred):
        super().__init__()
        self.var_name = var_name
        self.pred = pred

    def evaluate(self, prog):
        evaluated = self.pred.evaluate(prog)

        # Build a new automata with different edges
        bdict = spot.make_bdd_dict()
        new_aut = spot.make_twa_graph(bdict)

        aps = {}
        for ap in evaluated.ap():
            aps[ap.ap_name()] = buddy.bdd_ithvar(new_aut.register_ap(ap.ap_name()))

        new_aut.set_buchi() # Set the acceptance condition to the normal Buchi acceptance condition
        new_aut.new_states(evaluated.num_states())
        new_aut.set_init_state(0)

        for e in evaluated.edges():
            # Convert to a formula because formulas are nicer to work with than the bdd's
            formula = spot.formula(spot.bdd_format_formula(evaluated.get_dict(), e.cond))

            if_0 = self.substitute({self.var_name: spot.formula('0')}, formula)
            if_1 = self.substitute({self.var_name: spot.formula('1')}, formula)

            # The new edge condition should be:
            # [0/y]cond | [1/y]cond
            # where cond is the original condition. That is, the edge is taken if it holds with y being false or y being true.
            cond = self.create_edge_condition(evaluated, if_0) | self.create_edge_condition(evaluated, if_1)

            new_aut.new_edge(e.src, e.dst, cond, e.acc)

        return spot.minimize_obligation(new_aut)

    def substitute(self, subs, formula):
        if formula._is(spot.op_ap):
            if formula.ap_name() in subs:
                return subs[formula.ap_name()]
            else:
                return formula
        else:
            return formula.map(lambda x: self.substitute(subs, x))

    def create_edge_condition(self, bdd_dict, new_formula):
        return FormulaToBdd(bdd_dict, new_formula).translate()

    def __repr__(self):
        return '(∃{} ({}))'.format(self.var_name, self.pred)

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

