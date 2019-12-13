#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.ir import *

from pecan.tools.automaton_tools import TruthValue

class Type:
    def __init__(self):
        pass

    def get_restriction(self):
        return None

    def restrict(self, var):
        return None

    def __eq__(self, other):
        return other is not None and other.__class__ == self.__class__

    def __hash__(self):
        return 0 # There are no fields to hash

class AnyType(Type):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return 'any'

# These should only be present during type inference
class InferredType(Type):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return 'inferred'

class RestrictionType(Type):
    def __init__(self, restriction: Call):
        super().__init__()
        self.restriction = restriction

    def get_restriction(self):
        return self.restriction

    def restrict(self, var):
        if type(self.restriction) is Call:
            return self.restriction.with_args(self.restriction.args[1:]).insert_first(var)
        else:
            return self.restriction.insert_first(var)

    def __repr__(self):
        return repr(self.restriction.with_args(self.restriction.args[1:]))

    def __eq__(self, other):
        return other is not None and other.__class__ == self.__class__ and self.restriction == other.restriction

    def __hash__(self):
        return hash(self.restriction)

class TypeEnv:
    def __init__(self, prog):
        self.prog = prog
        self.type_env = {}
        self.unification = {}

    def __index__(self, idx):
        return self.type_env[idx]

    def __getitem__(self, item):
        return self.type_env[item]

    def __contains__(self, item):
        return item in self.type_env

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
            if t_a.name == t_b.name:
                if len(t_a.args) != len(t_b.args):
                    return None

                for arg1, arg2 in zip(t_a.args[1:], t_b.args[1:]):
                    if arg1.var_name != arg2.var_name:
                        return None

                return t_a
            else:
                # Unification didn't easily succeed, so drop down to actually using some theorem proving power to check
                # if the types are compatible
                temp_var = VarRef(self.prog.fresh_name())
                # TODO: Abstract out a subtyping checker thing here
                # TODO: Can probably optimize this by using spot's ability to check containment so we don't need to recompute/complement as much
                tval1 = TruthValue(Disjunction(Complement(t_a.subs_first(temp_var)), t_b.subs_first(temp_var))).truth_value(self.prog)
                tval2 = TruthValue(Disjunction(Complement(t_b.subs_first(temp_var)), t_a.subs_first(temp_var))).truth_value(self.prog)

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

class TypeInferer(IRTransformer):
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
        return Add(a, b).with_type(res_type)

    def transform_Sub(self, node: Sub):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Sub(a, b).with_type(res_type)

    def transform_Div(self, node: Div):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Div(a, b).with_type(res_type)

    def transform_IntConst(self, node: IntConst):
        return node.with_type(InferredType())

    def transform_VarRef(self, node: VarRef):
        if node.get_type() is not None:
            return node
        else:
            restrictions = self.prog.get_restrictions(node.var_name)
            if not node.var_name in self.type_env:
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

    def transform_Less(self, node: Less):
        a = self.transform(node.a)
        b = self.transform(node.b)
        res_type = self.type_env.unify(a, b)
        return Less(a.with_type(res_type), b.with_type(res_type))

    def transform_Exists(self, node: Exists):
        self.prog.enter_scope()

        if node.cond is not None:
            self.prog.restrict(node.var.var_name, node.cond)

        res = super().transform_Exists(node)

        self.prog.exit_scope()

        return res

    def transform_Call(self, node: Call):
        new_args = [self.transform(arg) for arg in node.args]

        temp_args = []
        for arg in new_args:
            if type(arg) is VarRef:
                temp_args.append(arg)
            else:
                new_var = VarRef(self.prog.fresh_name()).with_type(arg.get_type())
                temp_args.append(new_var)

        resolved_call = self.prog.lookup_dynamic_call(node.name, temp_args)
        resolved_pred = self.prog.lookup_pred_by_name(resolved_call.name)

        temp_type_env = TypeEnv(self.prog)

        final_args = []
        for formal, arg in zip(resolved_pred.args, new_args):
            found = False

            for formal_var, restriction in resolved_pred.arg_restrictions.items():
                if formal_var.var_name == formal.var_name:
                    found = True

                    restriction = restriction.pred.insert_first(formal)
                    res_type = temp_type_env.unify(formal.with_type(RestrictionType(restriction)), arg)
                    final_args.append(arg.with_type(res_type))

            if not found:
                final_args.append(arg)

        return Call(node.name, final_args)

    def transform_NamedPred(self, node):
        self.prog.enter_scope()

        for _, arg_restriction in node.arg_restrictions.items():
            arg_restriction.evaluate(self.prog)
        res = super().transform_NamedPred(node)

        self.prog.exit_scope()

        return res

