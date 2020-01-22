#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

from pecan.lang.ir.praline import *

from pecan.tools.automaton_tools import TruthValue

from pecan.settings import settings

class Check(Builtin):
    def __init__(self):
        super().__init__(PralineVar('check'), [PralineVar('t')])

    def evaluate(self, prog):
        pecan_node = prog.praline_lookup('t').evaluate(prog).pecan_term
        result = TruthValue(pecan_node).truth_value(prog)

        return PralineBool(result == 'true')

class ToString(Builtin):
    def __init__(self):
        super().__init__(PralineVar('toString'), [PralineVar('x')])

    def evaluate(self, prog):
        t = prog.praline_lookup('x').evaluate(prog)

        return PralineString(t.display())

class PralinePrint(Builtin):
    def __init__(self):
        super().__init__(PralineVar('print'), [PralineVar('s')])

    def evaluate(self, prog):
        print(prog.praline_lookup('s').evaluate(prog).display())
        return PralineBool(True)

class Emit(Builtin):
    def __init__(self):
        super().__init__(PralineVar('emit'), [PralineVar('pecanTerm')])

    def evaluate(self, prog):
        # TODO: Finish this
        term = prog.praline_lookup('pecanTerm').evaluate(prog).pecan_term
        settings.log(0, '[DEBUG] Emitted: "{}"'.format(term))
        prog.emit_definition(term)
        return PralineBool(True)

class FreshVar(Builtin):
    def __init__(self):
        super().__init__(PralineVar('freshVar'), [])

    def evaluate(self, prog):
        return PralineString(prog.fresh_name())

class ToChars(Builtin):
    def __init__(self):
        super().__init__(PralineVar('toChars'), [PralineVar('s')])

    def evaluate(self, prog):
        str_val = prog.praline_lookup('s').evaluate(prog).get_value()

        result = PralineList(None, None)

        for c in str_val[::-1]:
            result = PralineList(PralineString(c), result)

        return result

class Cons(Builtin):
    def __init__(self):
        super().__init__(PralineVar('cons'), [PralineVar('head'), PralineVar('tail')])

    def evaluate(self, prog):
        return PralineList(prog.praline_lookup('head').evaluate(prog), prog.praline_lookup('tail').evaluate(prog))

class AcceptingWord(Builtin):
    def __init__(self):
        super().__init__(PralineVar('acceptingWord'), [PralineVar('pecanTerm')])

    def evaluate(self, prog):
        acc_word = prog.praline_lookup('pecanTerm').evaluate(prog).pecan_term.evaluate(prog).accepting_word()

        if acc_word is None:
            return PralineList(None, None)

        acc_word.simplify()

        var_vals = {}
        var_names = []
        for formula in list(acc_word.prefix) + list(acc_word.cycle):
            for f in spot.atomic_prop_collect(spot.bdd_to_formula(formula)):
                var_names.append(f.ap_name())
        var_names = sorted(list(set(var_names)))
        prefixes = self.to_binary(var_names, acc_word.prefix)
        cycles = self.to_binary(var_names, acc_word.cycle)

        result = PralineList(None, None)
        for var_name in var_names[::-1]:
            word_tuple = PralineTuple([prefixes[var_name], cycles[var_name]])
            result = PralineList(PralineTuple([PralineString(var_name), word_tuple]), result)

        return result

    def to_binary(self, var_names, bdd_list):
        var_vals = {k: PralineList(None, None) for k in var_names}

        for bdd in bdd_list[::-1]:
            formula = spot.bdd_to_formula(bdd)

            next_vals = {}
            self.process_formula(next_vals, formula)

            # If we didn't find a value for a variable in this part of the formula, that means it can be either True or False.
            # We arbitrarily choose False.
            for var_name in var_names:
                var_vals[var_name] = PralineList(next_vals.get(var_name, PralineBool(False)), var_vals[var_name])


        return var_vals

    def process_formula(self, next_vals, formula):
        if formula._is(spot.op_ap):
            next_vals[formula.ap_name()] = PralineBool(True)
        elif formula._is(spot.op_Not):
            next_vals[formula[0].ap_name()] = PralineBool(False)
        elif formula._is(spot.op_And):
            for i in range(formula.size()):
                self.process_formula(next_vals, formula[i])
        elif formula._is(spot.op_tt):
            pass
        else:
            raise Exception('Cannot process formula: {}'.format(formula))

    def format_real(self, prefix, cycle):
        # It is possible for the whole number to be in the cycle (e.g., if the integral part is 0^w)
        if len(prefix) == 0:
            cycle_offset = 1
            sign = '+' if cycle[0] == '0' else '-'
        else:
            cycle_offset = 0
            sign = '+' if prefix[0] == '0' else '-'

        integral = ''
        # This is always just zeros, so don't bother showing it
        integral_repeat = ''
        fractional = ''
        fractional_repeat = ''

        # Need to keep track of which part will have
        fractional_modulus = 0
        for i, c in enumerate(prefix[1:]):
            if i % 2 == 0:
                fractional_modulus = 1
                fractional += c
            else:
                fractional_modulus = 0
                integral += c

        fractional_modulus = (fractional_modulus + cycle_offset) % 2
        for i, c in enumerate(cycle):
            if i % 2 == fractional_modulus:
                fractional_repeat += c
            else:
                integral_repeat += c

        # We store the integral part in LSD first
        integral = integral[::-1]
        integral_repeat = integral_repeat[::-1]

        if len(integral) > 0:
            return '{}{}.{}({})^w'.format(sign, integral, fractional, fractional_repeat)
        else:
            return '{}({})^w.{}({})^w'.format(sign, integral_repeat, fractional, fractional_repeat)

builtins = [
    Check().definition(),
    ToString().definition(),
    PralinePrint().definition(),
    Emit().definition(),
    FreshVar().definition(),
    AcceptingWord().definition(),
    ToChars().definition(),
    Cons().definition() ]

