#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast_transformer import AstTransformer
from pecan.lang.pecan_ast import *

from pecan.tools.automaton_tools import TruthValue

class Type:
    def __init__(self):
        pass

class AnyType(Type):
    def __init__(self):
        super().__init__()

class InferredType(Type):
    def __init__(self):
        super().__init__()

class RestrictionType(Type):
    def __init__(self, restriction):
        super().__init__()
        self.restriction = restriction

    # TODO: This should ideally be unnecessary (i.e., we should store restrictions so this is unnecessary)
    def get_restriction(self):
        if type(self.restriction) is Call:
            return self.restriction.with_args(self.restriction.args[1:])
        else:
            return self.restriction

class TypeEnv:
    def __init__(self, prog):
        self.prog = prog
        self.type_env = {}
        self.unification = {}

    def __index__(self, idx):
        return self.type_env[idx]

    def __getitem__(self, item):
        return self.type_env[item]

    def __setitem__(self, key, value):
        self.type_env[key] = value

    # TODO: At some point it would be nice to unify (haha) this code with the similar code in prog.py for looking up
    #  dynamic calls
    def unify(self, a, b):
        type_a = a.get_type()
        type_b = b.get_type()

        # TODO: Replace these exceptions (and all the others) with something that's more appropriate (probably a
        #  custom exception type)
        if isinstance(type_a, InferredType):
            return type_b
        elif isinstance(type_b, InferredType):
            return type_a
        elif isinstance(type_a, AnyType) and isinstance(type_b, AnyType):
            return AnyType()
        elif isinstance(type_a, AnyType):
            raise Exception(f'Cannot unify AnyType expression {a} with {b}')
        elif isinstance(type_b, AnyType):
            raise Exception(f'Cannot unify AnyType expression {b} with {a}')
        elif isinstance(type_a, RestrictionType) and isinstance(type_b, RestrictionType):
            return self.try_unify_type(a, type_a.get_restriction(), b, type_b.get_restriction())
        else:
            raise Exception(f'Unknown types {a} : {type_a} and {b} : {type_b}')

    def unify_with(self, t_a, t_b):
        if t_b in self.unification:
            return self.unification[t_b] == t_a
        else:
            self.unification[t_b] = t_a
            return True

    def unify_type(self, a, t_a, b, t_b):
        if type(t_a) is VarRef and type(t_b) is VarRef and t_a.var_name == t_b.var_name:
            return t_a
        elif type(t_a) is Call and type(t_b) is Call:
            if t_a.name != t_b.name or len(t_a.args) != len(t_b.args):
                return None

            for arg1, arg2 in zip(t_a.args, t_b.args):
                # These should all be strings or VarRefs # TODO: Make sure they're just VarRefs
                arg1_name = arg1.var_name if type(arg1) is VarRef else arg1
                arg2_name = arg2.var_name if type(arg2) is VarRef else arg2

                if arg1_name != arg2_name:
                    return None

            return t_a
        else:
            # Unification didn't easily succeed, so drop down to actually using some theorem proving power to check
            # if the types are compatible
            temp_var = VarRef(self.prog.fresh_name())
            tval1 = TruthValue(Implies(t_a.insert_first(temp_var), t_b.insert_first(temp_var))).truth_value(self.prog)
            tval2 = TruthValue(Implies(t_b.insert_first(temp_var), t_a.insert_first(temp_var))).truth_value(self.prog)

            if tval1 == 'true' or tval2 == 'true':
                return t_a
            elif tval1 == 'true':
                return t_b
            elif tval2 == 'true':
                return t_a
            else:
                return None

    def try_unify_type(self, a, t_a, b, t_b) -> Type:
        old_unification = dict(self.unification)
        result = self.unify_type(a, t_a, b, t_b)
        if result is not None:
            return RestrictionType(result)
        else:
            # Do it this way so we mutate `unification` itself, and we don't want to change it unless we successfully
            # unify
            self.unification.clear()
            self.unification.update(old_unification)
            raise Exception(f'Could not unify {a} : {t_a} and {b} : {t_b}')

    def remove(self, var_name):
        self.type_env.pop(var_name)

class TypeInferer(AstTransformer):
    def __init__(self, prog: Program):
        super().__init__()
        self.prog = prog
        self.type_env = TypeEnv(self.prog)

    def reset(self):
        self.type_env = TypeEnv(self.prog)
        return self

    def transform_Add(self, node: Add):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Add(a, b, param=node.param).with_type(res_type)

    def transform_Sub(self, node: Sub):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Sub(a, b, param=node.param).with_type(res_type)

    def transform_Mul(self, node: Mul):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Mul(a, b, param=node.param).with_type(res_type)

    def transform_Div(self, node: Div):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Div(a, b, param=node.param).with_type(res_type)

    def transform_IntConst(self, node: IntConst):
        return node.with_type(InferredType())

    def transform_VarRef(self, node: VarRef):
        restrictions = self.prog.get_restrictions(node.var_name)
        if len(restrictions) == 0:
            self.type_env[node.var_name] = AnyType()
        else:
            self.type_env[node.var_name] = RestrictionType(restrictions[-1]) # For now just use the last restriction
        return VarRef(node.var_name).with_type(self.type_env[node.var_name])

    def transform_Equals(self, node: Equals):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Equals(a.with_type(res_type), b.with_type(res_type))

    def transform_NotEquals(self, node: NotEquals):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return NotEquals(a.with_type(res_type), b.with_type(res_type))

    def transform_Less(self, node: Less):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Less(a.with_type(res_type), b.with_type(res_type))

    def transform_Greater(self, node: Greater):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Greater(a.with_type(res_type), b.with_type(res_type))

    def transform_LessEquals(self, node: LessEquals):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return LessEquals(a.with_type(res_type), b.with_type(res_type))

    def transform_GreaterEquals(self, node: GreaterEquals):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return GreaterEquals(a.with_type(res_type), b.with_type(res_type))

    def transform_Neg(self, node: Neg):
        a = self.transform(node.a)
        res_type = a.get_type()
        return Neg(a).with_type(res_type)

    def transform_Forall(self, node: Forall):
        if node.cond is None:
            self.type_env[node.var.var_name] = AnyType()
        else:
            self.type_env[node.var.var_name] = RestrictionType(node.cond)
        val = super().transform_Forall(node)
        self.type_env.remove(node.var.var_name)
        return val

    def transform_Exists(self, node: Exists):
        if node.cond is None:
            self.type_env[node.var.var_name] = AnyType()
        else:
            self.type_env[node.var.var_name] = RestrictionType(node.cond)
        val = super().transform_Exists(node)
        self.type_env.remove(node.var.var_name)
        return val

    def transform_Call(self, node: Call):
        # TODO: Handle the arg restrictions giving us additional type information
        new_args = [self.transform(arg) for arg in node.args]
        return Call(node.name, new_args)
