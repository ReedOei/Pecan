#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.tools.automaton_tools import Substitution, AutomatonTransformer, Projection
from pecan.lang.pecan_ir import *

#TODO: memoize same expressions
#TODO: Problem: can't change automaton for constants if definition of less_than or addition is changed in one run of Pecan.
class Add(BinaryIRExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def change_label(self, label): # for changing label to __constant#
        self.label = label

    def show(self):
        # The operands should always have the same type, but in the interest of debugging, we should display when this is not the case
        if self.a.get_type() == self.b.get_type():
            return '({} + {})'.format(self.a.show(), self.b.show())
        else:
            return '({} + {})'.format(self.a, self.b)

    def evaluate_node(self, prog):
        # if self.is_int:
        #     return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)

        if self.get_type() is not None:
            prog.restrict(self.label, self.get_type().restrict(self.label))

        aut_add = prog.call('adder', [val_a, val_b, self.label])
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_add, result)

        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return (result, self.label)

    def transform(self, transformer):
        return transformer.transform_Add(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) + self.b.evaluate_int(prog)

class Sub(BinaryIRExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate_node(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)

        if self.get_type() is not None:
            prog.restrict(self.label, self.get_type().restrict(self.label))

        aut_sub = prog.call('adder', [self.label, val_b, val_a])
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_sub, result)

        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return (result, self.label)

    def transform(self, transformer):
        return transformer.transform_Sub(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) - self.b.evaluate_int(prog)

class Mul(BinaryIRExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def evaluate_node(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        c = self.a.evaluate_int(prog)  # copy of a
        if c == 0:
            return IntConst(0).with_type(self.get_type()).evaluate(prog)

        power = self.b
        s = IntConst(0).with_type(self.get_type())
        while True:
            if c & 1 == 1:
                s = Add(power,s).with_type(self.get_type())
            c = c >> 1
            if c <= 0:
                break
            power = Add(power, power).with_type(self.get_type())

        return s.evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Mul(self)

    def show(self):
        return '({} * {})'.format(self.a, self.b)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) * self.b.evaluate_int(prog)


#TODO:
class Div(BinaryIRExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        if not self.is_int:
            raise NotImplementedError("Division with automaton hasn't been implemented, sorry. {}".format(self))
        if not self.b.is_int:
            raise AutomatonArithmeticError("Second argument of division must be an integer in {}".format(self))

    def show(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate_node(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)
        assert False
        b = self.b.evaluate_int(prog)
        if b == 1:
            return self.a.evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        # (aut_b, val_b) = IntConst(b).evaluate(prog)
        #TODO: change label, not finished
        (aut_div,val_div) = Mul(self.b,spot.formula('1').translate()).evaluate(prog)
        def build_div_formula(formula):
            return Substitution({val_div: spot.formula(val_a), 'a': spot.formula('{}_div_{}'.format(val_a,val_a))}).substitute(formula)
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_b, spot.product(aut_a, aut_div)), '{}_add_{}'.format(self.a,self.b))

    def evaluate_int(self, prog):
        assert self.is_int
        if self.a.evaluate_int(prog) % self.b.evaluate_int(prog) != 0:
                raise AutomatonArithmeticError("Division among integers must output an integer in {}".format(self))
        return self.a.evaluate_int(prog) // self.b.evaluate_int(prog)

    def transform(self, transformer):
        return transformer.transform_Div(self)

constants_map = {}
class IntConst(IRExpression):
    def __init__(self, val):
        super().__init__()
        self.val = val
        self.label = "__constant{}".format(self.val)

    def evaluate_node(self,prog):
        zero_const_var = VarRef("__constant0").with_type(self.get_type())
        zero_const = IntConst(0).with_type(self.get_type())
        one_const_var = VarRef("__constant1").with_type(self.get_type())

        b_const = VarRef('b').with_type(self.get_type())

        if self.get_type() is not None:
            prog.restrict(self.label, self.get_type().restrict(self.label))

        # TODO: Add a hash method to Type (see: type_inference.py) so that the constant map works properly
        if (self.val, self.get_type()) in constants_map:
            return constants_map[(self.val, self.get_type())]

        if self.val == 0:
            # Constant 0 is defined as 000000... TODO: Maybe allow users to define their own 0
            constants_map[(self.val, self.get_type())] = (spot.formula('G(~__constant0)').translate(), "__constant0")
        elif self.val == 1:
            leq = Disjunction(Less(one_const_var, b_const), Equals(one_const_var, b_const))
            formula_1 = Conjunction(Less(zero_const, one_const_var), Complement(Exists(self.get_type().restrict(b_const), Complement(Disjunction(Complement(Less(zero_const, b_const)), leq)))))

            if self.get_type().get_restriction() is not None:
                formula_1 = Conjunction(self.get_type().restrict(one_const_var), formula_1)

            constants_map[(self.val, self.get_type())] = (formula_1.evaluate(prog).postprocess('BA'), one_const_var.var_name)
        else:
            assert self.val >= 2, "constant here should be greater than or equal to 1, while it is {}".format(self.val)

            if self.val & (self.val - 1) == 0:
                half = IntConst(self.val // 2)
                result = Add(half, half).with_type(self.get_type())
            else:
                c = self.val
                power = 1
                while c != 1:
                    power  = power << 1
                    c = c >> 1
                result = Add(IntConst(power), IntConst(self.val - power)).with_type(self.get_type())

            result.change_label(self.label)
            result.is_int = False
            (result_aut, val) = result.evaluate(prog)
            constants_map[(self.val, self.get_type())] = (result_aut.postprocess('BA'), val)

        return constants_map[(self.val, self.get_type())]

    def evaluate_int(self, prog):
        return self.val

    def transform(self, transformer):
        return transformer.transform_IntConst(self)

    def show(self):
        return str(self.val)

class Equals(IRPredicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) == self.b.evaluate_int(prog) else spot.formula('0').translate()

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        eq_aut = spot.formula('G(({0} -> {1}) & ({1} -> {0}))'.format(val_a, val_b)).translate()
        result = spot.product(eq_aut, spot.product(aut_a, aut_b))
        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return result

    def transform(self, transformer):
        return transformer.transform_Equals(self)

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class Less(IRPredicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) < self.b.evaluate_int(prog) else spot.formula('0').translate()
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_less = prog.call('less', [val_a, val_b])
        result = spot.product(aut_a, aut_b)
        result = spot.product(aut_less, result)

        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return result

    def transform(self, transformer):
        return transformer.transform_Less(self)

    def __repr__(self):
        return '({} < {})'.format(self.a, self.b)

class AutomatonArithmeticError(Exception):
    pass

