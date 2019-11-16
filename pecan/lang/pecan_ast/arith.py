#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.pecan_ast.prog import *
from pecan.tools.automaton_tools import Substitution, AutomatonTransformer, Projection
from pecan.lang.pecan_ast.bool import *


base_2_addition = next(spot.automata("""
HOA: v1
States: 2
Start: 0
name: "Base2 Addition"
AP: 3 "a" "b" "c"
Acceptance: 1 Inf(0)
--BODY--
State: 0 {0}
[(!0&!1&!2)|(2&(0&!1|!0&1))] 0
[(0&1&!2)] 1
State: 1
[(0&1&2)|(!2&(0&!1|!0&1))] 1
[!0&!1&2] 0
--END--
"""))
#TODO: memoize same expressions
#TODO: detect and separate integer operations and Automaton operations
#TODO: do integer arithmetic before automaton arithmetic 
#TODO: add a flag for Buche automaton representing finite strings, so assert everything to be 0 eventually.
class Add(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def change_label(self, label): # for changing label to __constant#
        self.label = label

    def __repr__(self):
        return '({} + {})'.format(self.a, self.b)

    def evaluate(self, prog):
        # if type(self.a) is IntConst and type(self.b) is IntConst:
        #     return IntConst(self.a.evaluate_int() + self.b.evaluate_int())

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_add = base_2_addition #It is base 2 addition now TODO: get automaton
        def build_add_formula(formula): 
            return Substitution({'a': spot.formula(val_a), 'b': spot.formula(val_b),'c': spot.formula(self.label)}).substitute(formula)
        aut_add = AutomatonTransformer(aut_add, build_add_formula).transform()
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_add, result)
        # print(self, "result before projection:")
        # print(result.to_str('hoa'))
        # print()
        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        # print(self, "result")
        # print(result.to_str('hoa'))
        # print()
        return (result, self.label)

    

class Sub(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate(self, prog):
        # if type(self.a) is IntConst and type(self.b) is IntConst:
        #     return IntConst(self.a.evaluate_int() - self.b.evaluate_int()).evaluate(prog)
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_add = base_2_addition #It is base 2 addition now TODO: get automaton
        def build_sub_formula(formula): 
            return Substitution({'c': spot.formula(val_a), 'b':spot.formula(val_b), 'a': spot.formula(self.label)}).substitute(formula)
        aut_sub = AutomatonTransformer(aut_add, build_sub_formula).transform()
        
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_add, result)
        print(self, "result before projection:")
        print(result.to_str('hoa'))
        print()
        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add('val_a')
        if type(self.b) is not VarRef:
            proj_vars.add('val_b')
        result = Projection(result, proj_vars).project()
        print(self, "result after projection:")
        print(result.to_str('hoa'))
        print()
        return (result, self.label)

#TODO:
class Mul(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a = a
        self.b = b
        raise NotImplementedError("Division hasn't been implemented, sorry. {}".format(self))
        if type(self.a) is not IntConst:
            raise AutomatonArithmeticError("First argument of multiplication must be an integer in {}".format(self))

    def evaluate(self, prog):
        
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
        raise NotImplementedError("Division hasn't been implemented, sorry. {}".format(self))

    def __repr__(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if type(self.b) is not IntConst:
            raise AutomatonArithmeticError("Second argument of division must be an integer in {}".format(self))
        if type(self.a) is IntConst:
            if self.a % self.b != 0:
                raise AutomatonArithmeticError("Division among integers must output an integer in {}".format(self))
            return self.a // self.b
        if self.b == 1:
            return self.a.evaluate(prog)
       
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        #TODO: change label, not finished
        (aut_div,val_div) = Mul(self.b,spot.formula('1').translate()).evaluate(prog)
        def build_div_formula(formula): 
            return Substitution({val_div: spot.formula(val_a), 'a': spot.formula('{}_div_{}'.format(val_a,val_b))}).substitute(formula)
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_a, spot.product(aut_b, aut_div)), '{}_add_{}'.format(self.a,self.b))

#TODO: more memoization for calculated constants
constants_map = {0:(spot.formula('G(~__constant0)').translate(), "__constant0")}

class IntConst(Expression):
    # Constant 0 is defined as 000000...
    def __init__(self, val):
        super().__init__()
        self.val = val
        self.label = "__constant{}".format(self.val)

    def __repr__(self):
        return str(self.val)
    def evaluate(self,prog):
        if self.val in constants_map:
            return constants_map[self.val]
        if self.val == 1:
            # TODO: a = 1 iff (a>0 and (for all b > 0, b>=a))
            constants_map[1] = (spot.formula('{} & GX~{}'.format(self.label, self.label)).translate(), self.label)
            return constants_map[1]
        assert self.val >= 2, "constant here should be greater than or equal to 2, while it is {}".format(self.val)
        if (self.val & (self.val-1) == 0):
            result = Add(IntConst(self.val // 2), IntConst(self.val // 2))
        else:
            c = self.val   # copy of val
            power = 1
            while c != 1:
                power  = power << 1
                c = c // 2
            result = Add(IntConst(2 ** power), IntConst(self.val - 2 ** power))
        result.change_label(self.label)

        (result,val) = result.evaluate(prog)
        # TODO: Do I need to project here?
        # result = Projection(result, [self.label]).project()
        constants_map[self.val] = (result,val)
        print(self.val)
        print(constants_map[self.val][0].to_str('hoa'))
        print()
        return constants_map[self.val]

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
        # if type(self.a) is IntConst and type(self.b) is IntConst:
        #     return (spot.formula('1').translate(), self.__repr__) if self.a.evaluate() < self.b.evaluate() else (spot.formula('0').translate(), self.__repr__) 
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_less = '' #TODO: get automaton
        # assuming labels are "a<b"
        def build_less_formula(formula): 
            return Substitution({'a': spot.formula(val_a),'b':spot.formula(val_b)}).substitute(formula)
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
class NotImplementedError(Exception):
    pass

