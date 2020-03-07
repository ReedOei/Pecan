#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import time

from pecan.settings import settings

class IRNode:
    id = 0
    @staticmethod
    def fresh_name():
        label = f"__pecan_var{IRNode.id}"
        IRNode.id += 1
        return label

    def __init__(self):
        # TODO: detect used labels and avoid those
        self.label = None
        self.type = None

    def label_var(self):
        from pecan.lang.ir.prog import VarRef
        if self.label is None:
            self.label = IRNode.fresh_name()
        return VarRef(self.label).with_type(self.get_type())

    def with_type(self, new_type):
        self.type = new_type
        return self

    def get_type(self):
        return self.type

    def show_aut_stats(self, prog, aut, desc=None):
        sn, en = aut.num_states(), aut.num_edges()

        if desc is None:
            settings.log(1, lambda: self.indented(prog, 'Automaton has {} states and {} edges'.format(sn, en)))
        else:
            settings.log(1, lambda: self.indented(prog, 'Automaton has {} states and {} edges {}'.format(sn, en, desc)))

    def indented(self, prog, s):
        return '{}{}'.format(' ' * prog.eval_level, s)

    def simplify(self, prog, aut):
        self.show_aut_stats(prog, aut, desc='before simplify')

        # if aut.num_edges() < 1000000:
        aut.simplify_edges()
        self.show_aut_stats(prog, aut, desc='after simplify_edges')

        # if aut.num_states() < 100000:
        aut.simplify_states()
        self.show_aut_stats(prog, aut, desc='after simplify_states')

        aut.simplify_edges()
        self.show_aut_stats(prog, aut, desc='after simplify_edges')

        return aut

    def get_display_node(self, prog):
        return self

    def evaluate(self, prog):
        prog.eval_level += 1

        if settings.get_debug_level() > 0:
            start_time = time.time()
            # settings.log(0, lambda: self.indented(prog, 'Evaluating {}'.format(self))

        result = self.evaluate_node(prog)
        if type(result) is tuple:
            result = (self.simplify(prog, result[0]), result[1])
        else:
            result = self.simplify(prog, result)

        prog.eval_level -= 1

        if settings.get_debug_level() > 0:
            if type(result) is tuple:
                sn, en = result[0].num_states(), result[0].num_edges()
            else:
                sn, en = result.num_states(), result.num_edges()
            end_time = time.time()
            settings.log(0, lambda: self.indented(prog, '{} has {} states and {} edges ({:.2f} seconds)'.format(self.get_display_node(prog), sn, en, end_time - start_time)))

        return result

    def transform(self, transformer):
        return NotImplementedError('Transform not implemented for {}'.format(self.__class__.__name__))

    def evaluate_node(self, prog):
        raise NotImplementedError

class IRExpression(IRNode):
    def __init__(self):
        super().__init__()
        self.is_int = True

    def evaluate_node(self, prog):
        return None

    # This should be overriden by all expressions
    def show(self):
        raise NotImplementedError

    def __repr__(self):
        if self.type is None:
            return self.show()
        else:
            return f'{self.show()} : {self.get_type()}'

class UnaryIRExpression(IRExpression):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def with_type(self, new_type):
        self.a = self.a.with_type(new_type)
        return super().with_type(new_type)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a and self.get_type() == other.get_type()

    def __hash__(self):
        return hash((self.a, self.get_type()))

class BinaryIRExpression(IRExpression):
    def __init__(self, a, b):
        super().__init__()
        self.is_int = a.is_int and b.is_int
        self.a = a
        self.b = b

    def with_type(self, new_type):
        self.a = self.a.with_type(new_type)
        self.b = self.b.with_type(new_type)
        return super().with_type(new_type)

    def project_intermediates(self, prog, val_a, val_b, aut):
        from pecan.lang.ir.prog import VarRef

        proj_vars = set()

        if type(self.a) is not VarRef:
            proj_vars.add(val_a)

        if type(self.b) is not VarRef:
            proj_vars.add(val_b)

        return aut.project(proj_vars, prog.get_var_map())

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a and self.b == other.b and self.get_type() == other.get_type()

    def __hash__(self):
        return hash((self.a, self.b, self.get_type()))

class IRPredicate(IRNode):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        raise NotImplementedError

class BinaryIRPredicate(IRPredicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def project_intermediates(self, prog, val_a, val_b, aut):
        from pecan.lang.ir.prog import VarRef

        proj_vars = set()

        if type(self.a) is not VarRef:
            proj_vars.add(val_a)

        if type(self.b) is not VarRef:
            proj_vars.add(val_b)

        return aut.project(proj_vars, prog.get_var_map())

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a and self.b == other.b

    def __hash__(self):
        return hash((self.a, self.b))

class UnaryIRPredicate(IRPredicate):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a

    def __hash__(self):
        return hash(self.a)

