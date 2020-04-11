#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.ir import *

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
            return self.restriction.subs_last(var)
        else:
            return self.restriction.add_arg(var)

    def __repr__(self):
        return repr(self.restriction)

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

                for arg1, arg2 in zip(t_a.args[:-1], t_b.args[:-1]):
                    if arg1.var_name != arg2.var_name:
                        return None

                return t_a
            else:
                # Unification didn't easily succeed, so drop down to actually using some theorem proving power to check
                # if the types are compatible (e.g., subtyping check)
                temp_var = VarRef(self.prog.fresh_name())
                aut_a = t_a.subs_last(temp_var).evaluate(self.prog)
                aut_b = t_b.subs_last(temp_var).evaluate(self.prog)

                if aut_a.contains(aut_b) and aut_b.contains(aut_a):
                    return t_a
                elif aut_a.contains(aut_b):
                    return t_b
                elif aut_b.contains(aut_a):
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
                if len(restrictions) > 0:
                    self.type_env[node.var_name] = RestrictionType(restrictions[-1]) # For now just use the last restriction
                else:
                    self.type_env[node.var_name] = AnyType()
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

        for v, cond in zip(node.var_refs, node.conds):
            if cond is not None:
                self.prog.restrict(v.var_name, cond)

        res = super().transform_Exists(node)

        self.prog.exit_scope()

        return res

    def transform_Call(self, node: Call):
        new_args = [self.transform(arg) for arg in node.args]

        # Temp args is necessary, because the resolving dynamic calls only works with variables for now (TODO)
        arg_map = {}
        temp_args = []
        for arg in new_args:
            if type(arg) is VarRef:
                temp_args.append(arg)

                arg_map[arg] = arg
            else:
                new_var = VarRef(self.prog.fresh_name()).with_type(arg.get_type())
                temp_args.append(new_var)

                arg_map[new_var] = arg

        resolved_call = self.prog.lookup_dynamic_call(node.name, temp_args)
        resolved_pred = self.prog.lookup_pred_by_name(resolved_call.name)

        temp_type_env = TypeEnv(self.prog)

        final_args = []
        for formal, temp_arg in zip(resolved_pred.args, resolved_call.args):
            if temp_arg in arg_map:
                arg = arg_map[temp_arg]
            else:
                arg = temp_arg

            if formal.var_name in resolved_pred.restriction_env:
                # TODO: We choose the "last" one, because there is generally only one, and the last one is usually the most specific. This is not always right, however.
                restrictions = resolved_pred.restriction_env[formal.var_name]
                restriction = restrictions[-1]

                res_type = temp_type_env.unify(formal.with_type(RestrictionType(restriction)), arg)
                final_args.append(arg.with_type(res_type))
            else:
                final_args.append(arg)

        return Call(resolved_pred.name, final_args)

    def transform_NamedPred(self, node):
        self.prog.enter_scope(node.restriction_env)

        for _, arg_restriction in node.arg_restrictions.items():
            arg_restriction.evaluate(self.prog)

        res = super().transform_NamedPred(node)

        self.prog.exit_scope()

        return res

    def transform_FunctionExpression(self, node):
        temp_args = list(node.args)
        out_var_ref = VarRef(self.prog.fresh_name()).with_type(InferredType())
        temp_args[node.val_idx] = out_var_ref

        new_call = self.transform_Call(Call(node.pred_name, temp_args))

        res_type = None
        new_idx = -1
        for idx, arg in enumerate(new_call.args):
            if type(arg) is VarRef and arg.var_name == out_var_ref.var_name:
                res_type = arg.get_type()
                new_idx = idx

        if res_type is None:
            raise Exception('Missing output variable in resolved call: (was {}, resolved to {}, looking for {})'.format(node, new_call, out_var_ref))

        return FunctionExpression(new_call.name, new_call.args, new_idx).with_type(res_type)

