#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir.praline import *

from pecan.tools.automaton_tools import TruthValue

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

class StrLength(Builtin):
    def __init__(self):
        super().__init__(PralineVar('strLength'), [PralineVar('s')])

    def evaluate(self, prog):
        return PralineInt(len(prog.praline_lookup('s').get_value()))

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
        prog.emit_definition(term)
        return PralineBool(True)

class FreshVar(Builtin):
    def __init__(self):
        super().__init__(PralineVar('freshVar'), [])

    def evaluate(self, prog):
        return PralineVar(prog.fresh_name())

builtins = [
    StrLength().definition(),
    Check().definition(),
    ToString().definition(),
    PralinePrint().definition(),
    Emit().definition(),
    FreshVar().definition() ]

