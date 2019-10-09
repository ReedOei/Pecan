#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import spot

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
        # Basically just drop the relevant variable from each transition
        evaluated = self.pred.evaluate(prog)
        for e in evaluated.edges():
            formula = spot.formula(spot.bdd_format_formula(evaluated.get_dict(), e.cond))
            print('Formula:', formula)
            new_formula = self.ensure_formula_valid(self.remove_var(formula))
            print('New formula: ', new_formula)
            e.cond = self.create_edge_condition(evaluated, new_formula)
        return evaluated

    def ensure_formula_valid(self, formula):
        if formula is None:
            return spot.formula_tt()
        else:
            return formula

    def remove_var(self, formula):
        if formula._is(spot.op_ap): # op_ap is 'atomic proposition' (i.e., variable)
            if formula.ap_name() == self.var_name:
                return None
            else:
                return formula
        else:
            new_children = []
            for i in range(formula.size()):
                new_child = self.remove_var(formula[i])

                if new_child is not None:
                    new_children.append(new_child)

            return self.rebuild_formula(formula.kind(), new_children)

    def rebuild_binary(self, constr, children):
        if len(children) == 0:
            return None
        elif len(children) == 1:
            return children[0]
        else:
            return constr(children)

    def rebuild_formula(self, kind, new_children):
        if kind == spot.op_And:
            return self.rebuild_binary(spot.formula_And, new_children)
        elif kind == spot.op_Or:
            return self.rebuild_binary(spot.formula_Or, new_children)
        elif kind == spot.op_Not:
            if len(new_children) == 0:
                return None
            else:
                return spot.formula_Not(new_children[0])
        elif kind == spot.op_tt:
            return spot.formula_tt()
        elif kind == spot.op_ff:
            return spot.formula_ff()
        else:
            raise Exception('Unhandled formula kind: {}'.format(kind))


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

