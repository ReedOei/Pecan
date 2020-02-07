#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir.base import *

from pecan.tools.labeled_aut_converter import *

class PralineTerm(IRNode):
    def __init__(self):
        super().__init__()
        self.evaluated_value = None

    def is_bool(self):
        return False

    def is_int(self):
        return False

    def is_string(self):
        return False

    # TODO: This function and the whole type system really ought to be improved
    def typeof(self):
        if self.is_bool():
            return "bool"
        elif self.is_int():
            return "int"
        elif self.is_string():
            return "string"
        else:
            return "unknown"

    def display(self):
        return repr(self)

class PralineDisplay(IRNode):
    def __init__(self, term):
        super().__init__()
        self.term = term

    def evaluate(self, prog):
        prog.enter_praline_env()
        print(self.term.evaluate(prog).display())
        prog.exit_praline_env()

    def transform(self, transformer):
        return transformer.transform_PralineDisplay(self)

    def __repr__(self):
        return 'Display {} .'.format(self.term)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.term == other.term

    def __hash__(self):
        return hash(self.term)

class PralineExecute(IRNode):
    def __init__(self, term):
        super().__init__()
        self.term = term

    def evaluate(self, prog):
        prog.enter_praline_env()
        self.term.evaluate(prog)
        prog.exit_praline_env()

    def transform(self, transformer):
        return transformer.transform_PralineExecute(self)

    def __repr__(self):
        return 'Execute {} .'.format(self.term)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.term == other.term

    def __hash__(self):
        return hash(self.term)

class PralineDef(IRNode):
    def __init__(self, name, args, body):
        super().__init__()
        self.name = name
        self.args = args
        self.body = body

    def evaluate(self, prog):
        res = Closure({}, self.args, self.body)
        prog.praline_define(self.name.var_name, res)

    def transform(self, transformer):
        return transformer.transform_PralineDef(self)

    def __repr__(self):
        return 'Define {} {} := {} .'.format(self.name, self.args, self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.name == other.name and self.args == other.args and self.body == other.body

    def __hash__(self):
        return hash((self.name, self.args, self.body))

class PralineVar(PralineTerm):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def evaluate(self, prog):
        return prog.praline_lookup(self.var_name).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_PralineVar(self)

    def __repr__(self):
        return '{}'.format(self.var_name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var_name == other.var_name

    def __hash__(self):
        return hash((self.var_name))

class PralineApp(PralineTerm):
    def __init__(self, receiver, arg):
        super().__init__()
        self.receiver = receiver
        self.arg = arg

    def evaluate(self, prog):
        return self.receiver.evaluate(prog).apply(prog, self.arg.evaluate(prog)).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_PralineApp(self)

    def __repr__(self):
        return '({} {})'.format(self.receiver, self.arg)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.receiver == other.receiver and self.arg == other.arg

    def __hash__(self):
        return hash((self.receiver, self.arg))

class PralineBinaryOp(PralineTerm):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a and self.b == other.b

    def __hash__(self):
        return hash((self.a, self.b))

class PralineAdd(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineAdd(self)

    def __repr__(self):
        return '({} + {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() + eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineDiv(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineDiv(self)

    def __repr__(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() // eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineSub(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineSub(self)

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() - eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineMul(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineMul(self)

    def __repr__(self):
        return '({} * {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() * eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineExponent(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineExponent(self)

    def __repr__(self):
        return '({} ^ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value()**eval_b.get_value())
        elif eval_a.is_string() and eval_b.is_string():
            return PralineString(eval_a.get_value() + eval_b.get_value()) # + is for string concatenation
        else:
            raise TypeError('Both operands should be integers or strings in "{}", but they are ({} : {}) and ({} : {}), respectively.'.format(self, eval_a, eval_a.typeof(), eval_b, eval_b.typeof()))

class PralineUnaryOp(PralineTerm):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a

    def __hash__(self):
        return hash((self.a))

class PralineNeg(PralineUnaryOp):
    def __init__(self, a):
        super().__init__(a)

    def transform(self, transformer):
        return transformer.transform_PralineNeg(self)

    def __repr__(self):
        return '(-{})'.format(self.a)

    def evaluate(self, prog):
        temp = self.a.evaluate(prog)

        if not temp.is_int():
            raise TypeError('operand should evaluate to an integer in "{}"'.format(temp, self))

        return PralineInt(-temp.get_value())

class PralineList(PralineBinaryOp):
    def __init__(self, head, tail):
        super().__init__(head, tail)

    def transform(self, transformer):
        return transformer.transform_PralineList(self)

    def __repr__(self):
        if self.a is None:
            return '[]'
        else:
            return '({} :: {})'.format(self.a, self.b)

    def display(self):
        elems = []
        cur = self

        while cur.a is not None:
            elems.append(cur.a)
            cur = cur.b

        return '[{}]'.format(','.join([e.display() for e in elems]))

    def evaluate(self, prog):
        if self.a is not None:
            new_a = self.a.evaluate(prog)
        else:
            new_a = None

        if self.b is not None:
            new_b = self.b.evaluate(prog)
        else:
            new_b = None

        return PralineList(new_a, new_b)

class PralineMatch(PralineTerm):
    def __init__(self, t, arms):
        super().__init__()
        self.t = t
        self.arms = arms

    def transform(self, transformer):
        return transformer.transform_PralineMatch(self)

    def __repr__(self):
        return 'match {} with\n{}\nend'.format(self.t, '\n'.join(map(repr, self.arms)))

    def evaluate(self, prog):
        eval_t = self.t.evaluate(prog)

        for arm in self.arms:
            match_env = arm.match(eval_t)

            if match_env is not None:
                prog.praline_local_define_all(match_env)
                result = arm.expr.evaluate(prog)
                prog.praline_local_cleanup(match_env.keys())
                return result

        raise Exception('Inexhaustive match arms in "{}" (got "{}")'.format(self, eval_t))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.t == other.t and self.arms == other.arms

    def __hash__(self):
        return hash((self.t, self.arms))

class PralineMatchArm(IRNode):
    def __init__(self, pat, expr):
        super().__init__()
        self.pat = pat
        self.expr = expr

    def match(self, term):
        return self.pat.match(term)

    def transform(self, transformer):
        return transformer.transform_PralineMatchArm(self)

    def __repr__(self):
        return 'case {} => {}'.format(self.pat, self.expr)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.pat == other.pat and self.expr == other.expr

    def __hash__(self):
        return hash((self.pat, self.expr))

class PralineMatchPat(IRNode):
    def __init__(self):
        super().__init__()

class PralineMatchInt(PralineMatchPat):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def match(self, term):
        if term.is_int() and term.get_value() == self.val:
            return {}
        else:
            return None

    def transform(self, transformer):
        return transformer.transform_PralineMatchInt(self)

    def __repr__(self):
        return 'PralineMatchInt({})'.format(self.val)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.val))

class PralineMatchString(PralineMatchPat):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def match(self, term):
        if term.is_string() and term.get_value() == self.val:
            return {}
        else:
            return None

    def transform(self, transformer):
        return transformer.transform_PralineMatchString(self)

    def __repr__(self):
        return 'PralineMatchString({})'.format(self.val)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.val))

class PralineMatchList(PralineMatchPat):
    def __init__(self, head, tail):
        super().__init__()
        self.head = head
        self.tail = tail

    def match(self, term):
        if not type(term) is PralineList:
            return None

        if self.head is None or term.a is None:
            if self.head is None and term.a is None:
                return {}
            else:
                return None

        head_match_env = self.head.match(term.a)

        if head_match_env is None:
            return None

        tail_match_env = self.tail.match(term.b)

        if tail_match_env is None:
            return None

        head_match_env.update(tail_match_env)

        return head_match_env

    def transform(self, transformer):
        return transformer.transform_PralineMatchList(self)

    def __repr__(self):
        return 'PralineMatchList({}, {})'.format(self.head, self.tail)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.head == other.head and self.tail == other.tail

    def __hash__(self):
        return hash((self.head, self.tail))

class PralineMatchTuple(PralineMatchPat):
    def __init__(self, vals):
        super().__init__()
        self.vals = vals

    def transform(self, transformer):
        return transformer.transform_PralineMatchTuple(self)

    def __repr__(self):
        return 'PralineMatchTuple({})'.format(','.join(map(repr, self.vals)))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.vals == other.vals

    def __hash__(self):
        return hash((self.vals))

    def match(self, term):
        if not type(term) is PralineTuple:
            return None

        if len(self.vals) != len(term.vals):
            return None

        match_env = {}

        for pat, t in zip(self.vals, term.vals):
            match_env.update(pat.match(t))

        return match_env

class PralineMatchVar(PralineMatchPat):
    def __init__(self, var):
        super().__init__()
        self.var = var

    def match(self, term):
        return {self.var: term}

    def transform(self, transformer):
        return transformer.transform_PralineMatchVar(self)

    def __repr__(self):
        return '{}'.format(self.var)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var == other.var

    def __hash__(self):
        return hash((self.var))

class PralineIf(PralineTerm):
    def __init__(self, cond, e1, e2):
        super().__init__()
        self.cond = cond
        self.e1 = e1
        self.e2 = e2

    def transform(self, transformer):
        return transformer.transform_PralineIf(self)

    def __repr__(self):
        return '(if {} then {} else {})'.format(self.cond, self.e1, self.e2)

    def evaluate(self, prog):
        cond_eval = self.cond.evaluate(prog)
        if cond_eval.is_bool():
            if cond_eval.get_value():
                return self.e1.evaluate(prog)
            else:
                return self.e2.evaluate(prog)
        else:
            raise TypeError('cond should evaluate to a bool in "{}", got "{}"'.format(self, cond_eval))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.cond == other.cond and self.e1 == other.e1 and self.e2 == other.e2

    def __hash__(self):
        return hash((self.cond, self.e1, self.e2))

class PralinePecanTerm(PralineTerm):
    def __init__(self, pecan_term):
        super().__init__()
        self.pecan_term = pecan_term

    def transform(self, transformer):
        return transformer.transform_PralinePecanTerm(self)

    def __repr__(self):
        return '{{ {} }}'.format(self.pecan_term)

    def evaluate(self, prog):
        from pecan.lang.ir_substitution import IRSubstitution
        from pecan.lang.praline_to_pecan import PralineToPecan

        temp_node = PralinePecanTerm(PralineToPecan().transform(IRSubstitution(prog.praline_env_clone()).transform(self.pecan_term)))

        return prog.type_infer(temp_node)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.pecan_term == other.pecan_term

    def __hash__(self):
        return hash((self.pecan_term))

class PralineLambda(PralineTerm):
    def __init__(self, params, body):
        super().__init__()
        self.params = params
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLambda(self)

    def __repr__(self):
        return '(\\ {} -> {})'.format(self.params, self.body)

    def evaluate(self, prog):
        return Closure(prog.praline_env_clone(), self.params, self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.params == other.params and self.body == other.body

    def __hash__(self):
        return hash((self.params, self.body))

class PralineLetPecan(PralineTerm):
    def __init__(self, var_name, pecan_term, body):
        super().__init__()
        self.var_name = var_name
        self.pecan_term = pecan_term
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLetPecan(self)

    def __repr__(self):
        return '(let {} be {} in {})'.format(self.var_name, self.pecan_term, self.body)

    def evaluate(self, prog):
        result_node = self.pecan_term.evaluate(prog).pecan_term

        from pecan.lang.ir.prog import AutLiteral
        prog.praline_local_define(self.var_name, PralinePecanTerm(AutLiteral(result_node.evaluate(prog))))
        result = self.body.evaluate(prog)
        prog.praline_local_cleanup([self.var_name])

        return result

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var_name == other.var_name and self.pecan_term == other.pecan_term and self.body == other.body

    def __hash__(self):
        return hash((self.var_name, self.pecan_term, self.body))

class PralineLet(PralineTerm):
    def __init__(self, var_name, expr, body):
        super().__init__()
        self.var_name = var_name
        self.expr = expr
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLet(self)

    def __repr__(self):
        return '(let {} := {} in {})'.format(self.var_name, self.expr, self.body)

    def evaluate(self, prog):
        prog.praline_local_define(self.var_name, self.expr.evaluate(prog))
        result = self.body.evaluate(prog)
        prog.praline_local_cleanup([self.var_name])
        return result

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var_name == other.var_name and self.expr == other.expr and self.body == other.body

    def __hash__(self):
        return hash((self.var_name, self.expr, self.body))

class PralineTuple(PralineTerm):
    def __init__(self, vals):
        super().__init__()
        self.vals = vals

    def transform(self, transformer):
        return transformer.transform_PralineTuple(self)

    def __repr__(self):
        return '({})'.format(','.join(map(repr, self.vals)))

    def evaluate(self, prog):
        return PralineTuple([v.evaluate(prog) for v in self.vals])

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.vals == other.vals

    def __hash__(self):
        return hash((self.vals))

    def display(self):
        return '({})'.format(','.join([v.display() for v in self.vals]))

class Closure(PralineTerm):
    def __init__(self, env, args, body):
        super().__init__()
        self.env = env
        self.args = args
        self.body = body

    def evaluate(self, prog):
        if self.args: # If we still require more arguments
            return self
        else: # Evaluate as though we are in the environment specified
            prog.praline_local_define_all(self.env)
            result = self.body.evaluate(prog)
            prog.praline_local_cleanup(self.env.keys())
            return result

    def transform(self, transformer):
        return transformer.transform_Closure(self)

    def __repr__(self):
        return 'Closure({}, {}, {})'.format(self.env, self.args, self.body)

    def apply(self, prog, arg):
        if not self.args:
            raise Exception('Closure accepts no arguments!')

        new_env = dict(self.env)
        new_env[self.args[0].var_name] = arg

        if len(self.args) == 1:
            prog.enter_praline_env(new_env)
            result = self.body.evaluate(prog)
            prog.exit_praline_env()
            return result
        else:
            return Closure(new_env, self.args[1:], self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.env == other.env and self.args == other.args and self.body == other.body

    def __hash__(self):
        return hash((self.args, self.body))

class PralineInt(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineInt(self)

    def __repr__(self):
        return 'PralineInt({})'.format(self.val)

    def evaluate(self, prog):
        return self

    def get_value(self):
        return self.val

    def is_int(self):
        return True

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.args, self.body))

    def display(self):
        return '{}'.format(self.val)

class PralineString(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineString(self)

    def __repr__(self):
        return 'PralineString({})'.format(self.val)

    def evaluate(self, prog):
        return self

    def get_value(self):
        return self.val

    def is_string(self):
        return True

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.val))

    def display(self):
        return '{}'.format(self.val)

class PralineBool(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineBool(self)

    def __repr__(self):
        return 'PralineBool({})'.format(self.val)

    def evaluate(self, prog):
        return self

    def get_value(self):
        return self.val

    def is_bool(self):
        return True

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.args, self.body))

    def display(self):
        if self.val:
            return 'true'
        else:
            return 'false'

class Builtin(PralineTerm):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def transform(self, transformer):
        return transformer.transform_Builtin(self)

    def __repr__(self):
        return 'BUILTIN({})'.format(self.name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.name == other.name and self.args == other.args

    def __hash__(self):
        return hash(self.name)

    def definition(self):
        return PralineDef(self.name, self.args, self)

class PralineDo(PralineTerm):
    def __init__(self, terms):
        super().__init__()
        self.terms = terms

    def transform(self, transformer):
        return transformer.transform_PralineDo(self)

    def __repr__(self):
        return 'do\n    {}'.format('\n    '.join(map(repr, self.terms)))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.terms == other.terms

    def __hash__(self):
        return hash((self.terms))

    def evaluate(self, prog):
        result = None

        for term in self.terms:
            result = term.evaluate(prog)

        return result

class PralineAutomaton(PralineTerm):
    def __init__(self, input_names, input_bases, states, state_map):
        super().__init__()
        self.input_names = input_names
        self.input_bases = input_bases
        self.alphabet_line = ' '.join('{' + ','.join(map(str, range(base))) + '}' for base in input_bases)

        self.states = states
        self.state_map = state_map
        self.state_idx = len(self.states)

    def transform(self, transformer):
        return transformer.transform_PralineAutomaton(self)

    def __repr__(self):
        return 'PralineAutomaton({}, {}, {}, {})'.format(self.input_names, self.input_bases, self.state_map, self.states)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.input_bases == other.input_bases and self.alphabet_line == other.alphabet_line and self.states == other.states and self.state_idx == other.state_idx and self.state_map == other.state_map and self.input_names == other.input_names

    def __hash__(self):
        return hash((self.alphabet_line, self.state_idx, len(self.states)))

    def evaluate(self, prog):
        return self

    def add_state(self, state_line):
        new_state = State(self.state_idx, state_line)
        self.states.append(new_state)
        self.state_map[new_state.label] = self.state_idx

        self.state_idx += 1

        return self

    def add_transition(self, state_label, transition_line):
        if state_label not in self.state_map:
            raise Exception('No state "{}" in {}'.format(state_label, self))

        self.states[self.state_map[state_label]].add_transition(Transition(transition_line))

        return self

    def build(self):
        return build_aut(self.alphabet_line, self.states, self.state_map, self.input_names)

