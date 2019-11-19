#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.pecan_ast.prog import *
from pecan.tools.automaton_tools import Substitution, AutomatonTransformer, Projection
from pecan.lang.pecan_ast.bool import *
from pecan.lang.pecan_ast.quant import Forall

#TODO: memoize same expressions
class Add(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def change_label(self, label): # for changing label to __constant#
        self.label = label

    def __repr__(self):
        return '({} + {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_add = prog.call(prog.context['adder'], [val_a, val_b, self.label])
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_add, result)
        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return (result, self.label)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) + self.b.evaluate_int(prog)


class Sub(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_sub = prog.call(prog.context['adder'], [self.label, val_b, val_a])
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_sub, result)

        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return (result, self.label)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) - self.b.evaluate_int(prog)

#TODO:
class Mul(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.a = a
        self.b = b
        if not self.is_int:
            raise NotImplementedError("Multiplication with automaton hasn't been implemented, sorry. {}".format(self))
        if not self.a.is_int:
            raise AutomatonArithmeticError("First argument of multiplication must be an integer in {}".format(self))

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).evaluate(prog)

        c = self.a.evaluate_int(prog)  # copy of a
        # TODO: memoize
        power =  self.b
        sum = IntConst(0)
        while c > 0:
            if c & 1 == 1:
                sum = Add(sum,power)
            c = c >> 1
            power = Add(power,power)
        # TODO: substitute label
        return sum.evaluate(prog)

    def __repr__(self):
        return '({} * {})'.format(self.a, self.b)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) * self.b.evaluate_int(prog)
#TODO:
class Div(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.a = a
        self.b = b
        if not self.is_int:
            raise NotImplementedError("Division with automaton hasn't been implemented, sorry. {}".format(self))
        if not self.b.is_int:
            raise AutomatonArithmeticError("Second argument of division must be an integer in {}".format(self))

    def __repr__(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).evaluate(prog)
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


constants_map = {0:(spot.formula('G(~__constant0)').translate(), "__constant0")}
class IntConst(Expression):
    # Constant 0 is defined as 000000...
    def __init__(self, val, param=None):
        super().__init__()
        self.val = val
        self.label = "__constant{}".format(self.val)

    def __repr__(self):
        return str(self.val)
    def evaluate(self,prog):
        if self.val in constants_map:
            return constants_map[self.val]
        if self.val == 1:
            formula_1 = Conjunction(Less(IntConst(0),VarRef("__constant1")), Forall('b', Implies(Less(IntConst(0), VarRef('b')), \
                                    LessEquals(VarRef('__constant1'), VarRef("b")))))
            constants_map[1] = (formula_1.evaluate(prog), "__constant1")
            return constants_map[1]
        assert self.val >= 2, "constant here should be greater than or equal to 2, while it is {}".format(self.val)
        if (self.val & (self.val-1) == 0):
            result = Add(IntConst(self.val // 2), IntConst(self.val // 2))
        else:
            c = self.val
            power = 1
            while c != 1:
                power  = power << 1
                c = c >> 1
            result = Add(IntConst(power), IntConst(self.val - power))
        result.change_label(self.label)
        result.is_int = False
        (result,val) = result.evaluate(prog)
        constants_map[self.val] = (result,val)
        return constants_map[self.val]

    def evaluate_int(self, prog):
        return self.val

class Equals(Predicate):
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

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) != self.b.evaluate_int(prog) else spot.formula('0').translate()
        return Complement(Equals(self.a, self.b)).evaluate(prog)

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

class Less(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b
    def evaluate(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) < self.b.evaluate_int(prog) else spot.formula('0').translate()
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_less = prog.call(prog.context['less'], [val_a, val_b])
        result = spot.product(aut_a, aut_b)
        result = spot.product(aut_less, result)

        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return result

    def __repr__(self):
        return '({} < {})'.format(self.a, self.b)

class Greater(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} > {})'.format(self.a, self.b)

    def evaluate(self, prog):
        return Less(self.b,self.a).evaluate(prog)

class LessEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} ≤ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) <= self.b.evaluate_int(prog) else spot.formula('0').translate()
        return Disjunction(Less(self.a,self.b),Equals(self.a,self.b)).evaluate(prog)

class GreaterEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} ≥ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) >= self.b.evaluate_int(prog) else spot.formula('0').translate()
        return Disjunction(Less(self.b,self.a),Equals(self.a,self.b)).evaluate(prog)

class Neg(Expression): # Should this be allowed?

    def __init__(self, a):
        super().__init__()
        self.a = a

    def __repr__(self):
        return '(-{})'.format(self.a)

    def evaluate(self, prog):
        if self.a.is_int:
            return IntConst(self.evaluate_int(prog)).evaluate(prog)
        raise AutomatonArithmeticError("Should not negate automaton in {}".format(self))
        return Sub(IntConst(0),self.a).evaluate(prog)

    def evaluate_int(self, prog):
        assert self.is_int
        return -self.a.evaluate_int(prog)

class AutomatonArithmeticError(Exception):
    pass
class NotImplementedError(Exception):
    pass



# is this something that we will want? Probably not, I'm not implementing it for now.
class Index(Expression):
    def __init__(self, var_name, index_expr):
        super().__init__()
        self.var_name = var_name
        self.index_expr = index_expr
        self.is_int = False
        raise NotImplementedError("Indexing hasn't been implemented, sorry. {}".format(self))

    def __repr__(self):
        return '({}[{}])'.format(self.var_name, self.index_expr)
