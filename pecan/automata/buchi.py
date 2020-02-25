#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import spot

from pecan.automata.automaton import Automaton, FalseAutomaton
from pecan.tools.shuffle_automata import ShuffleAutomata
from pecan.utility import VarMap
from pecan.settings import settings

def merge(merge_f, aut_a, aut_b):
    if aut_a.num_states() < aut_b.num_states():
        merged_var_map, subs = aut_b.get_var_map().merge_with(aut_a.get_var_map())
        # print('merge(a into b)', merged_var_map, subs)
        new_a = BuchiAutomaton(aut_a.get_aut(), aut_a.get_var_map()).ap_substitute(subs)
        new_b = aut_b
    else:
        merged_var_map, subs = aut_a.get_var_map().merge_with(aut_b.get_var_map())
        # print('merge(b into a)', merged_var_map, subs)
        new_a = aut_a
        new_b = BuchiAutomaton(aut_b.get_aut(), aut_b.get_var_map()).ap_substitute(subs)

    return BuchiAutomaton(merge_f(new_a.get_aut(), new_b.get_aut()), merged_var_map)

def merge_maps(aut, map_a: VarMap, map_b: VarMap):
    merged_var_map, subs = map_a.merge_with(map_b)
    return BuchiAutomaton(aut, merged_var_map).ap_substitute(subs)

class BuchiAutomaton(Automaton):
    id = 0
    @staticmethod
    def fresh_ap():
        label = f"__ap{BuchiAutomaton.id}"
        BuchiAutomaton.id += 1
        return label

    @classmethod
    def as_buchi(cls, aut):
        if aut.get_aut_type() == 'buchi':
            return aut
        elif aut.get_aut_type() == 'true':
            return BuchiAutomaton(spot.translate('1'), VarMap())
        elif aut.get_aut_type() == 'false':
            return BuchiAutomaton(spot.translate('0'), VarMap())
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

    def with_var_map(self, new_var_map):
        self.var_map = new_var_map

        for v, aps in self.var_map.items():
            for ap in aps:
                self.aut.register_ap(ap)

        return self

    def make_empty_aut(self):
        return BuchiAutomaton.as_buchi(FalseAutomaton()).with_var_map(self.var_map)

    def conjunction(self, other):
        return merge(spot.product, self, other)

    def disjunction(self, other):
        return merge(spot.product_or, self, other)

    def complement(self):
        return BuchiAutomaton(spot.complement(self.get_aut()), self.var_map)

    def relabel(self):
        new_aps = {}
        for ap in self.aut.ap():
            new_aps[ap.ap_name()] = self.fresh_ap()

        #.print('relabel()', new_aps)
        return self.ap_substitute(new_aps)

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

    def ap_substitute(self, ap_subs):
        # If we try something like [x/x]P, just don't do anything
        ap_subs = {k: v for k, v in ap_subs.items() if k != v}

        if not ap_subs:
            return self

        bdd_subs = {self.aut.register_ap(k): v for k, v in ap_subs.items()}

        # print('ap_sub postprocess:', self.aut.num_states(), self.aut.num_edges(), list(map(str, self.aut.ap())), self.aut.acc())
        # self.aut.merge_edges()
        # self.aut.merge_states()
        # print('ap_sub postprocess (post merge):', self.aut.num_states(), self.aut.num_edges(), list(map(str, self.aut.ap())), self.aut.acc())

        if settings.get_simplication_level() > 0:
            self.postprocess()

        new_var_map = VarMap()
        to_register = []
        for v, aps in self.var_map.items():
            new_var_map[v] = []
            for ap in aps:
                # Get the new name of this ap, or just the ap if the name didn't get
                new_ap = ap_subs.get(ap, ap)

                new_var_map[v].append(new_ap)
                to_register.append(new_ap)

        # print('ap_subs()', ap_subs, self.var_map, new_var_map)

        new_aut = buchi_transform(self.aut, Substitution(bdd_subs))

        for new_ap in to_register:
            new_aut.register_ap(new_ap)

        return BuchiAutomaton(new_aut, new_var_map) #.postprocess()

    def project(self, var_refs, env_var_map):
        from pecan.lang.ir.prog import VarRef
        aps = []
        pecan_var_names = []

        for v in var_refs:
            if type(v) is VarRef:
                aps.extend(self.var_map[v.var_name])
                pecan_var_names.append(v.var_name)

        result = self.ap_project(aps)

        if settings.get_simplication_level() > 0:
            result = result.postprocess()

        for var_name in pecan_var_names:
            # It may not be there (e.g., it's perfectly valid to do "exists x. y = y", even if it's pointless)
            if var_name in result.get_var_map():
                result.get_var_map().pop(var_name)

            if var_name in env_var_map:
                env_var_map.pop(var_name)

        return result

    def ap_project(self, aps):
        if not aps:
            return self

        # print('ap_project()', aps)

        # Do a quick check here to simplify if we're empty; the emptiness checking algorithm is very fast (can be done in linear time)
        # Compared to the cost of postprocessing (depends on the underlying automaton, but generally atrocious)
        # this is very cheap, and gives us an easy simplification if it works.
        if self.aut.is_empty():
            return self.make_empty_aut()

        res_aut = self.aut
        for ap in aps:
            # print('projecting:', ap)

            res_aut = buchi_transform(res_aut, BuchiProjection(res_aut, ap))

            # print('is_empty', res_aut.is_empty())

        return BuchiAutomaton(res_aut, self.get_var_map())

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
        acc_word = self.get_aut().accepting_word()

        if acc_word is None:
            return None

        acc_word.simplify()

        var_names = []
        for formula in list(acc_word.prefix) + list(acc_word.cycle):
            for f in spot.atomic_prop_collect(spot.bdd_to_formula(formula)):
                var_names.append(f.ap_name())

        var_names = sorted(list(set(var_names)))
        prefixes = self.to_binary(var_names, acc_word.prefix)
        cycles = self.to_binary(var_names, acc_word.cycle)

        ap_result = {}
        for var_name in var_names:
            ap_result[var_name] = (prefixes[var_name], cycles[var_name])

        result = {}
        for var, aps in self.var_map.items():
            result[var] = [ap_result[ap] for ap in aps]
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
        return BuchiAutomaton.as_buchi(other)

    def postprocess(self):
        if not self.aut.is_sba():
            self.aut = self.aut.postprocess('BA') # Ensure that the automata we have is a Buchi (possible nondeterministic) automata
        return self

    def simplify(self):
        return self.postprocess()

    def shuffle(self, is_disj, other):
        # Don't need to convert ourselves, but may need to convert other aut to Buchi
        aut_a = self
        aut_b = self.convert(other)

        return merge_maps(ShuffleAutomata(aut_a.get_aut(), aut_b.get_aut()).shuffle(is_disj), aut_a.get_var_map(), aut_b.get_var_map())

    def to_str(self):
        return 'VAR_MAP: {}\n{}'.format(self.var_map.to_str(), self.aut.to_str('hoa'))

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

