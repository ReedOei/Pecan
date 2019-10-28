#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.pecan_ast.prog import *
from pecan.tools.automaton_tools import Substitution, AutomatonTransformer
from pecan.lang.pecan_ast.bool import *

#TODO: preassign label to expression
class Add(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} + {})'.format(self.a, self.b)

    def evaluate(self, prog):
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_add = '' #TODO: get automaton
        # Assuming label "a+b=c"
        def build_add_formula(self, formula): 
            return Substitution({'a': val_a, 'b': val_b,'c': '{}{}'.format(self.a,self.b)}).substitute(formula)
        aut_add = AutomatonTransformer(aut_add, build_add_formula).transform()
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_a, spot.product(aut_b, aut_add)), '{}_add_{}'.format(self.a,self.b))

    

class Sub(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate(self, prog):
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_sub = '' #TODO: get automaton
        # Assuming label "a+b=c"
        def build_sub_formula(self, formula): 
            #TODO: make it one dictionary
            return Substitution({'c': val_a}).substitute(Substitution({'b': val_b}).substitute(Substitution({'a': '{}{}'.format(self.a,self.b)}).substitute(formula)))
        aut_sub = AutomatonTransformer(aut_sub, build_sub_formula).transform()
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_a, spot.product(aut_b, aut_add)), '{}_add_{}'.format(self.a,self.b))


class Mul(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def evaluate(self, prog):
        if self.a is not IntConst:
            raise AutomatonArithmeticError("First argument of multiplication must be an integer in " + self.__repr__())
        if self.b is IntConst:
            return self.a.evaluate_int()*self.b.evaluate_int()

        c = self.a.evaluate_int()  # copy of a
        # TODO: memoize
        power =  self.b
        sum = IntConst(0)
        while c > 0:
            if c & 1 == 1:
                sum = Add(sum,power)
            c = c >> 1
            power = Add(power,power)
        # TODO: substitute label
        return sum.evaluate()

    def __repr__(self):
        return '({} * {})'.format(self.a, self.b)

#TODO:
class Div(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.b is not int:
            raise AutomatonArithmeticError("Second argument of division must be an integer in " + self.__repr__())
        if self.a is int:
            if self.a % self.b != 0:
                raise AutomatonArithmeticError("Division among integers must output an integer in " + self.__repr__())
            return self.a // self.b
        if self.b == 1:
            return self.a.evaluate(prog)
       
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        #TODO: change label, not finished
        (aut_div,val_div) = Mul(b,spot.formula('1'.format(val_a,val_b)).translate())
        def build_div_formula(self, formula): 
            return Substitution({val_div: val_a}).substitute(Substitution({'a': '{}_div_{}'.format(val_a,val_b)}).substitute(formula)))
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_a, spot.product(aut_b, aut_add)), '{}_add_{}'.format(self.a,self.b))

        return 

class IntConst(Expression):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def __repr__(self):
        return str(self.val)
    def evaluate(self):
        if self.val is not IntConst:
            raise AutomatonArithmeticError("Constants need to be integers" + self.__repr__())
        if self.val == 0:
            return (spot.formula('G(!n0)').translate(),"n0")
        if self.val == 1:
            return (spot.formula('one G(!n1)').translate(), "n1")

        c = self.val  # copy of a
        #TODO: memoize
        power =  IntConst(1)
        sum = IntConst(0)
        while c > 0:
            if c & 1 == 1:
                sum = Add(sum,power)
            c = c >> 1
            power = Add(power,power)
        return sum.evaluate()

    def evaluate_int(self):
        return self.val

# is this something that we will want? I'm leaving it here for now
class Index(Expression):
    def __init__(self, var_name, index_expr):
        super().__init__()
        self.var_name = var_name
        self.index_expr = index_expr

    def __repr__(self):
        return '({}[{}])'.format(self.var_name, self.index_expr)

class Less(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b
    def evaluate(self, prog):
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_less = '' #TODO: get automaton
        # assuming labels are "a<b"
        def build_less_formula(self, formula): 
            return Substitution({'a': val_a}).substitute(Substitution({'b': val_b}).substitute(formula))
        aut_less = AutomatonTransformer(aut_less, build_less_formula).transform()
        return spot.product(aut_a, spot.product(aut_b, aut_less))
    
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

class Neg(Expression): # Should this be allowed?

    def __init__(self, a):
        super().__init__()
        self.a = a

    def __repr__(self):
        return '(-{})'.format(self.a)

    def evaluate(self, prog):
        return Sub(IntConst(0),self.a).evaluate(prog)


class LessEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} ≤ {})'.format(self.a, self.b)
    
    def evaluate(self, prog):
        return Disjunction(Less(self.a,self.b),Equals(self.a,self.b)).evaluate(prog)

class GreaterEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} ≥ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        return Disjunction(Less(self.b,self.a),Equals(self.a,self.b)).evaluate(prog)

class AutomatonArithmeticError(Exception):
    pass