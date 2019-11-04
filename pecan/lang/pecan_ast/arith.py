#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from lang.pecan_ast.prog import *
from tools.automaton_tools import Substitution, AutomatonTransformer
from lang.pecan_ast.bool import *

base_2_addition = spot.automata("""
HOA: v1
States: 2
Start: 1
name: "Hello world"
acc-name: "Buchi"
AP: 3 "a" "b" "c"
Acceptance: 1 Inf(0)
--BODY--
State: 0 {0}
[(!a&!b&!c)|(c&(a&!b|!a&b)] 0
[(!a&!b&c)] 1
State: 1
[(a&b&c)|(!c&(a&!b|!a&b)] 1
[a&b&!c] 0
--END--
""")
#TODO: preassign label to expression
#TODO: memoize same expressions
#TODO: detect and separate integer operations and Automaton operations
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
        aut_add = base_2_addition #It is base 2 addition now TODO: get automaton
        # Assuming label "a+b=c"
        def build_add_formula(self, formula): 
            return Substitution({'a': val_a, 'b': val_b,'c': self.label}).substitute(formula)
        aut_add = AutomatonTransformer(aut_add, build_add_formula).transform()
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_a, spot.product(aut_b, aut_add)), self.label)

    

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
            return Substitution({'c': val_a, 'b':val_b, 'a': self.label}).substitute(formula)
        aut_sub = AutomatonTransformer(aut_sub, build_sub_formula).transform()
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_a, spot.product(aut_b, aut_sub)), self.label)


class Mul(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def evaluate(self, prog):
        if type(self.a) is not IntConst:
            raise AutomatonArithmeticError("First argument of multiplication must be an integer in " + self.__repr__())
        if type(self.b) is IntConst:
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
        if type(self.b) is not int:
            raise AutomatonArithmeticError("Second argument of division must be an integer in " + self.__repr__())
        if type(self.a) is int:
            if self.a % self.b != 0:
                raise AutomatonArithmeticError("Division among integers must output an integer in " + self.__repr__())
            return self.a // self.b
        if self.b == 1:
            return self.a.evaluate(prog)
       
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        #TODO: change label, not finished
        (aut_div,val_div) = Mul(self.b,spot.formula('1').translate()).evaluate(prog)
        def build_div_formula(self, formula): 
            return Substitution({val_div: val_a, 'a': '{}_div_{}'.format(val_a,val_b)}).substitute(formula)
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_a, spot.product(aut_b, aut_div)), '{}_add_{}'.format(self.a,self.b))

#TODO: more memoization for calculated constants
class IntConst(Expression):
    # Constant 0 is defined as 000000...
    constants_map = {0:(spot.formula('G(!__constant0)').translate(), "__constant0")}
    def __init__(self, val):
        super().__init__()
        self.val = val
        if type(self.val) is not int:
            raise AutomatonArithmeticError("Constants need to be integers" + self.__repr__())
        self.label = "__constant{}".format(self.val)

    def __repr__(self):
        return str(self.val)
    def evaluate(self):
        if self.val == 0:
            return IntConst.constants_map[0]
        if self.val == 1:
            # TODO: a = 1 iff (a>0 and (for all b > 0, b>=a))
            IntConst.constants_map[1] = (spot.formula('{} G(!{}})', self.label).translate(), self.label)
            return IntConst.constants_map[1]

        c = self.val  # copy of val
        power =  IntConst(1)
        sum = IntConst(0)
        while c > 0:
            if c & 1 == 1:
                sum = Add(sum,power)
            c = c >> 1
            power = Add(power,power)

        IntConst.constants_map[self.val] = sum.evaluate()
        return IntConst.constants_map[self.val]

    def evaluate_int(self):
        return self.val

# is this something that we will want? Probably not, I'm not implementing it for now.
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
            return Substitution({'a': val_a,'b':val_b}).substitute(formula)
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
        raise AutomatonArithmeticError('Cannot do negation on automaton. {}'.format(self))
        # TODO: allow negation on IntConst
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
