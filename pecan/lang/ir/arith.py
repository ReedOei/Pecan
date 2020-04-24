#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

# From: https://stackoverflow.com/a/57027610/1498618
def is_power_of_two(n):
    return (n != 0) and (n & (n-1) == 0)

# TODO: memoize same expressions
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
        if self.is_int and self.evaluate_int(prog) >= 0:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)

        aut_add = prog.call('adder', [val_a, val_b, self.label_var()])

        result = self.project_intermediates(prog, val_a, val_b, aut_a & aut_b & aut_add)

        return (result, self.label_var())

    def transform(self, transformer):
        return transformer.transform_Add(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) + self.b.evaluate_int(prog)

class Sub(BinaryIRExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def show(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate_node(self, prog):
        if self.is_int and self.evaluate_int(prog) >= 0:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)

        aut_sub = prog.call('adder', [self.label_var(), val_b, val_a])

        result = self.project_intermediates(prog, val_a, val_b, aut_a & aut_b & aut_sub)
        return (result, self.label_var())

    def transform(self, transformer):
        return transformer.transform_Sub(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) - self.b.evaluate_int(prog)

#TODO: Implement division if/when possible
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
        if self.is_int and self.evaluate_int(prog) >= 0:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        assert False

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
        if self.val < 0:
            return Sub(IntConst(0), IntConst(-self.val)).with_type(self.get_type()).evaluate(prog)

        if (self.val, self.get_type()) in constants_map:
            return constants_map[(self.val, self.get_type())]

        if self.val == 0:
            res = prog.call('zero', [self.label_var()])
            constants_map[(self.val, self.get_type())] = (res, self.label_var())
        elif self.val == 1:
            res = prog.lookup_dynamic_call('one', [self.label_var()])

            # This means we didn't find a user-defined "one", so just use the default expression
            if res.name == 'one':
                b_const = VarRef(prog.fresh_name()).with_type(self.get_type())
                zero_const = IntConst(0).with_type(self.get_type())

                leq = Disjunction(Less(self.label_var(), b_const), Equals(self.label_var(), b_const))
                b_in_0_1 = Conjunction(Less(zero_const, b_const), Less(b_const, self.label_var()))
                formula_1 = Conjunction(Less(zero_const, self.label_var()), Complement(Exists([b_const], [self.get_type().restrict(b_const)], b_in_0_1)))
                constants_map[(self.val, self.get_type())] = (formula_1.evaluate(prog), self.label_var())
            else:
                res = prog.call('one', [self.label_var()])
                constants_map[(self.val, self.get_type())] = (res, self.label_var())
        else:
            assert self.val >= 2, "constant here should be greater than or equal to 2, while it is {}".format(self.val)

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

            # because the powers of two get used so much, it is advantageous to make sure they are as small
            # as possible by postprocessing them
            if is_power_of_two(self.val):
                result_aut.postprocess()

            constants_map[(self.val, self.get_type())] = (result_aut, val)

        return constants_map[(self.val, self.get_type())]

    def evaluate_int(self, prog):
        return self.val

    def transform(self, transformer):
        return transformer.transform_IntConst(self)

    def show(self):
        return str(self.val)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val and self.get_type() == other.get_type()

    def __hash__(self):
        return hash(self.val)

class Equals(BinaryIRPredicate):
    def __init__(self, a, b):
        super().__init__(a, b)

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return BoolConst(self.a.evaluate_int(prog) == self.b.evaluate_int(prog)).evaluate(prog)

        print(self.a, self.a.get_type())
        print(self.b, self.a.get_type())
        input('BLAH')

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)

        eq_aut = prog.call('equal', [val_a, val_b])

        return self.project_intermediates(prog, val_a, val_b, eq_aut & aut_a & aut_b)

    def transform(self, transformer):
        return transformer.transform_Equals(self)

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class Less(BinaryIRPredicate):
    def __init__(self, a, b):
        super().__init__(a, b)

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return BoolConst(self.a.evaluate_int(prog) < self.b.evaluate_int(prog)).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)

        aut_less = prog.call('less', [val_a, val_b])

        return self.project_intermediates(prog, val_a, val_b, aut_a & aut_b & aut_less)

    def transform(self, transformer):
        return transformer.transform_Less(self)

    def __repr__(self):
        return '({} < {})'.format(self.a, self.b)

class FunctionExpression(IRExpression):
    def __init__(self, pred_name, args, val_idx):
        super().__init__()
        self.is_int = False
        self.pred_name = pred_name
        self.args = args
        self.val_idx = val_idx # the index of the "return value" of the function
        # TODO: Warn users if the function is not a "true" function

    def evaluate_node(self, prog):
        return_val = VarRef(prog.fresh_name()).with_type(self.args[self.val_idx].get_type())
        self.args[self.val_idx] = return_val
        return Call(self.pred_name, self.args).evaluate(prog), return_val

    # Transforms the function expression into a regular call, with the result going into the variable provided.
    # For example: if we have something like P() = x, we probably want to transform this into just P(x)
    def to_call(self, result_var):
        self.args[self.val_idx] = result_var
        return Call(self.pred_name, self.args)

    def transform(self, transformer):
        return transformer.transform_FunctionExpression(self)

    def show(self):
        temp_args = list(map(repr, self.args))
        temp_args[self.val_idx] = 'out({})'.format(self.args[self.val_idx])
        return '{}({})'.format(self.pred_name, ', '.join(temp_args))

class AutomatonArithmeticError(Exception):
    pass

