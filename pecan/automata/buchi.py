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

<<<<<<< HEAD
    def __init__(self, aut, var_map):
=======
    id = 0
    def fresh_ap(self):
        name = f'__ap{BuchiAutomaton.id}'
        BuchiAutomaton.id += 1
        return name

    def __init__(self, aut):
>>>>>>> origin/master
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

    def call(self, arg_map, env_var_map):
        call_var_map = {}
        arg_var_map = {}
        ap_subs = {}

        for formal_arg, actual_arg in arg_map.items():
            if actual_arg in call_var_map:
                for a, b in zip(self.get_var_map()[formal_arg], call_var_map[actual_arg]):
                    ap_subs[a] = b
            else:
                call_var_map[actual_arg] = self.get_var_map()[formal_arg]

            if actual_arg not in env_var_map:
                env_var_map[actual_arg] = [ self.fresh_ap() for i in self.get_var_map()[formal_arg] ]

            arg_var_map[actual_arg] = env_var_map[actual_arg]

        # print('call()', arg_map, env_var_map, arg_var_map, call_var_map, ap_subs)

        return merge(self.ap_substitute(ap_subs).aut, arg_var_map, call_var_map)

        # TODO: Remove this if it's no longer needed
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

    def relabel(self, arguments=None):
        new_aps = {}
        for ap in self.aut.ap():
            new_aps[ap.ap_name()] = self.fresh_ap()

        for ap in arguments or []:
            new_aps[ap] = self.fresh_ap()

        return new_aps, self.substitute(new_aps)

    def substitute(self, subs):
<<<<<<< HEAD
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
=======
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
>>>>>>> origin/master

        # print('substitute()', self.get_var_map(), subs, new_var_map, ap_subs)

        return BuchiAutomaton(self.get_aut(), new_var_map).ap_substitute(ap_subs)

    def ap_substitute(self, subs):
        clean_subs(subs)

        if len(subs) == 0:
            return self

        return BuchiTransformer(self, Substitution(subs)).transform()

    def project(self, var_refs, env_var_map):
        from pecan.lang.ir.prog import VarRef
<<<<<<< HEAD
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

            if var_name in env_var_map:
                env_var_map.pop(var_name)

        return result
=======
        var_names = [v.var_name for v in var_refs if type(v) is VarRef]

        res_aut = self.aut.postprocess('BA')
        for var_name in var_names:
            if not res_aut.is_sba():
                res_aut = res_aut.postprocess('BA')

            res_aut = buchi_transform(res_aut, BuchiProjection(res_aut, var_name))

        return BuchiAutomaton(res_aut)
>>>>>>> origin/master

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

<<<<<<< HEAD
class BuchiTransformer:
    def __init__(self, original_aut, builder):
        self.original_aut = original_aut
        self.builder = builder
=======
    def save(self, filename):
        self.aut.save(filename)

    def to_str(self):
        return self.aut.to_str('hoa')
>>>>>>> origin/master

def buchi_transform(original_aut, builder):
    # Build a new automata with different edges
    new_aut = spot.make_twa_graph()

<<<<<<< HEAD
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
=======
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
>>>>>>> origin/master

class Substitution(Builder):
    def __init__(self, subs):
        self.subs = subs

<<<<<<< HEAD
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

=======
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
>>>>>>> origin/master
