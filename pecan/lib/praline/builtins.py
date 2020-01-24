#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

from pecan.lang.ir.praline import *

from pecan.settings import settings

def as_praline(val):
    if type(val) is list:
        result = PralineList(None, None)

        for v in val[::-1]:
            result = PralineList(as_praline(v), result)

        return result
    elif type(val) is str:
        return PralineString(val)
    elif type(val) is bool:
        return PralineBool(val)
    elif type(val) is int:
        return PralineInt(val)
    elif type(val) is tuple:
        return PralineTuple([as_praline(v) for v in val])
    else:
        raise Exception("Can't convert {} ({}) to a Praline value".format(type(val), val))

class Check(Builtin):
    def __init__(self):
        super().__init__(PralineVar('check'), [PralineVar('t')])

    def evaluate(self, prog):
        pecan_node = prog.praline_lookup('t').evaluate(prog).pecan_term
        result = pecan_node.evaluate(prog).truth_value()

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

        result = PralineList(None, None)
        for var_name, vs in acc_word.items():
            result = PralineList(PralineTuple([PralineString(var_name), as_praline(vs)]), result)

        return result

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

class Compare(Builtin):
    def __init__(self):
        super().__init__(PralineVar('compare'), [PralineVar('a'), PralineVar('b')])

    def evaluate(self, prog):
        a_val = prog.praline_lookup('a').evaluate(prog).get_value()
        b_val = prog.praline_lookup('b').evaluate(prog).get_value()

        if a_val < b_val:
            return PralineInt(-1)
        elif a_val > b_val:
            return PralineInt(1)
        else:
            return PralineInt(0)

class Equal(Builtin):
    def __init__(self):
        super().__init__(PralineVar('equal'), [PralineVar('a'), PralineVar('b')])

    def evaluate(self, prog):
        a_val = prog.praline_lookup('a').evaluate(prog)
        b_val = prog.praline_lookup('b').evaluate(prog)
        return PralineBool(a_val == b_val)

builtins = [
    Check().definition(),
    ToString().definition(),
    PralinePrint().definition(),
    Emit().definition(),
    FreshVar().definition(),
    AcceptingWord().definition(),
    ToChars().definition(),
    Cons().definition(),
    Compare().definition(),
    Equal().definition() ]

