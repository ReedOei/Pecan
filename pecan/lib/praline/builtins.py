#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

import pathlib

from pecan.lang.ir.praline import *
from pecan.lang.ir import AutLiteral
from pecan.lib.plot import BuchiPlotter

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

def as_python(val, expected=None):
    if isinstance(val, PralineList):
        if expected is None or isinstance(val, expected):
            result = []
            while val.a is not None:
                result.append(as_python(val.a))
                val = val.b

            return result
    elif isinstance(val, PralineString):
        if expected is None or isinstance(val, expected):
            return val.val
    elif isinstance(val, PralineBool):
        if expected is None or isinstance(val, expected):
            return val.val
    elif isinstance(val, PralineInt):
        if expected is None or isinstance(val, expected):
            return val.val
    elif isinstance(val, PralineTuple):
        if expected is None or isinstance(val, expected):
            return tuple([as_python(v) for v in val.vals])
    # Currently, this is **only** for unwrapping automata
    elif isinstance(val, PralinePecanLiteral):
        if expected is None or isinstance(val, expected):
            return val.get_term()
    else:
        raise Exception("Can't convert {} ({}) to a Python value".format(type(val), val))

    if expected is not None:
        raise Exception('Expected type was {}, but got value: {}'.format(expected, val))
    else:
        raise Exception('Unexpected error while converting {} to a Python value (expected type: {})'.format(val, expected))

class TruthValue(Builtin):
    def __init__(self):
        super().__init__(PralineVar('truthValue'), [PralineVar('t')])

    def evaluate(self, prog):
        pecan_node = prog.praline_lookup('t').evaluate(prog).get_term()
        res = pecan_node.evaluate(prog)
        if isinstance(res, tuple):
            tval = res[0].truth_value()
        else:
            tval = res.truth_value()
        return PralineString(tval)

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
        term = prog.praline_lookup('pecanTerm').evaluate(prog).get_term()
        settings.log(0, lambda: '[DEBUG] Emitted: "{}"'.format(term))
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
        res = prog.praline_lookup('pecanTerm').evaluate(prog).get_term().evaluate(prog)

        if isinstance(res, tuple):
            acc_word = res[0].accepting_word()
        else:
            acc_word = res.accepting_word()

        result = PralineList(None, None)
        for var_name, vs in acc_word.items():
            result = PralineList(PralineTuple([PralineString(var_name), as_praline(vs)]), result)

        return result

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


class MkAutomaton(Builtin):
    def __init__(self):
        super().__init__(PralineVar('mkAut'), [PralineVar('inputNames'), PralineVar('inputBases')])

    def evaluate(self, prog):
        input_names = as_python(prog.praline_lookup('inputNames').evaluate(prog))
        input_bases = as_python(prog.praline_lookup('inputBases').evaluate(prog))
        return PralineAutomaton(input_names, input_bases, [], {})

class AddState(Builtin):
    def __init__(self):
        super().__init__(PralineVar('addState'), [PralineVar('aut'), PralineVar('stateLabel'), PralineVar('isAccepting')])

    def evaluate(self, prog):
        aut = prog.praline_lookup('aut').evaluate(prog)
        label = prog.praline_lookup('stateLabel').evaluate(prog).get_value()
        isAccepting = prog.praline_lookup('isAccepting').evaluate(prog).get_value()

        state_str = f'{label}: {1 if isAccepting else 0}'
        aut.add_state(state_str)

        return aut

class AddTransition(Builtin):
    def __init__(self):
        super().__init__(PralineVar('addTransition'), [PralineVar('aut'), PralineVar('src'), PralineVar('dst'), PralineVar('syms')])

    def evaluate(self, prog):
        aut = prog.praline_lookup('aut').evaluate(prog)
        src = prog.praline_lookup('src').evaluate(prog).get_value()
        dst = prog.praline_lookup('dst').evaluate(prog).get_value()
        syms = prog.praline_lookup('syms').evaluate(prog).get_value()

        aut.add_transition(src, '{} -> {}'.format(syms, dst))

        return aut

class BuildAut(Builtin):
    def __init__(self):
        super().__init__(PralineVar('buildAut'), [PralineVar('aut')])

    def evaluate(self, prog):
        aut = prog.praline_lookup('aut').evaluate(prog)
        return PralinePecanTerm(AutLiteral(aut.build()))

class AutToStr(Builtin):
    def __init__(self):
        super().__init__(PralineVar('autToStr'), [PralineVar('aut')])

    def evaluate(self, prog):
        aut = prog.praline_lookup('aut').evaluate(prog)
        if type(aut) is PralinePecanLiteral:
            term = aut.get_term()
            if type(term) is AutLiteral:
                return PralineString(term.aut.to_str())
            else:
                raise Exception('Expected an AutLiteral but got {}'.format(term))
        else:
            raise Exception('Expected a PralinePecanTerm, but got: {}'.format(aut))

class WriteFile(Builtin):
    def __init__(self):
        super().__init__(PralineVar('writeFile'), [PralineVar('filepath'), PralineVar('str')])

    def evaluate(self, prog):
        filepath = prog.praline_lookup('filepath').evaluate(prog).get_value()
        s = prog.praline_lookup('str').evaluate(prog).get_value()

        with open(filepath, 'w') as f:
            f.write(s)

        prog.add_generate_file(filepath)

        return PralineBool(True)

class ReadFile(Builtin):
    def __init__(self):
        super().__init__(PralineVar('readFile'), [PralineVar('filepath')])

    def evaluate(self, prog):
        filepath = prog.praline_lookup('filepath').evaluate(prog).get_value()
        with open(filepath, 'r') as f:
            return PralineString(f.read())

class DeleteFile(Builtin):
    def __init__(self):
        super().__init__(PralineVar('deleteFile'), [PralineVar('filepath')])

    def evaluate(self, prog):
        filepath = prog.praline_lookup('filepath').evaluate(prog).get_value()
        pathlib.Path(filepath).unlink()
        return PralineBool(True)

class Split(Builtin):
    def __init__(self):
        super().__init__(PralineVar('splitStr'), [PralineVar('sep'), PralineVar('s')])

    def evaluate(self, prog):
        sep = prog.praline_lookup('sep').evaluate(prog).get_value()
        s = prog.praline_lookup('s').evaluate(prog).get_value()

        return as_praline(s.split(sep))

#plot(peano, alphabet_x=3, alphabet_y=3, alphabet_t=9, layer=2, color_by_axis="t")
#plot(hilbert, alphabet_x=2, alphabet_y=2, alphabet_t=4, layer=2, color_by_axis="t")

class Plot(Builtin):
    def __init__(self):
        super().__init__(PralineVar('plot'), [PralineVar('options'), PralineVar('numSystems'), PralineVar('aut')])

    def evaluate(self, prog):
        options = dict(as_python(prog.praline_lookup('options').evaluate(prog)))
        num_systems = dict(as_python(prog.praline_lookup('numSystems').evaluate(prog)))
        term = as_python(prog.praline_lookup('aut').evaluate(prog), PralinePecanLiteral)
        settings.log(lambda: '[INFO] Plotting {} using numeration systems {} with options: {}'.format(term, num_systems, options))
        aut = term.evaluate(prog)
        plotter = BuchiPlotter(prog, num_systems, aut, **options)
        plotter.plot()
        return PralineBool(True)

builtins = [
    TruthValue().definition(),
    ToString().definition(),
    Split().definition(),
    PralinePrint().definition(),
    Emit().definition(),
    FreshVar().definition(),
    AcceptingWord().definition(),
    ToChars().definition(),
    Cons().definition(),
    Compare().definition(),
    Equal().definition(),
    MkAutomaton().definition(),
    AddState().definition(),
    AddTransition().definition(),
    BuildAut().definition(),
    AutToStr().definition(),
    DeleteFile().definition(),
    WriteFile().definition(),
    ReadFile().definition(),
    Plot().definition()
]

