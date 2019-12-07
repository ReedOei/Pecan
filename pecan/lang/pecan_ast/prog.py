#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import time
import os
from functools import reduce

from lark import Lark, Transformer, v_args
import spot

from pecan.tools.automaton_tools import AutomatonTransformer, Substitution
from pecan.lang.pecan_ast.base import *

class VarRef(Expression):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name
        self.is_int = False

    def insert_first(self, arg_name):
        return Call(self.var_name, [arg_name])

    def evaluate(self, prog):
        # The automata accepts everything (because this isn't a predicate)
        return spot.formula('1').translate(), self.var_name

    def transform(self, transformer):
        return transformer.transform_VarRef(self)

    def show(self):
        return str(self.var_name)

class AutLiteral(Predicate):
    def __init__(self, aut):
        super().__init__()
        self.aut = aut
        self.is_int = False

    def evaluate(self, prog):
        return self.aut

    def transform(self, transformer):
        return transformer.transform_AutLiteral(self)

    def show(self):
        return repr(self)

    def __repr__(self):
        return 'AUTOMATON LITERAL' # TODO: Maybe improve this?

class SpotFormula(Predicate):
    def __init__(self, formula_str):
        super().__init__()
        self.formula_str = formula_str

    def evaluate(self, prog):
        return spot.translate(self.formula_str)

    def transform(self, transformer):
        return transformer.transform_SpotFormula(self)

    def __repr__(self):
        return 'LTL({})'.format(self.formula_str)

class Match:
    def __init__(self, pred_name=None, pred_args=None, match_any=False):
        if pred_args is None:
            pred_args = []

        self.pred_name = pred_name
        self.pred_args = pred_args
        self.match_any = match_any

    def arity(self):
        return len(self.pred_args)

    def unify(self, other):
        if other.match_any:
            return self
        if self.match_any:
            return other

        new_args = []
        if self.pred_name != other.pred_name or self.arity() != other.arity():
            raise Exception(f'Could not unify {self} and {other}')

        for arg1, arg2 in zip(self.pred_args, other.pred_args):
            if arg1 == 'any' and arg2 == 'any':
                new_args.append('any')
            elif arg1 == 'any' and arg2 != 'any':
                new_args.append(arg2)
            elif arg1 != 'any' and arg2 == 'any':
                new_args.append(arg1)
            else:
                if arg1 == arg2:
                    new_args.append(arg1)
                else:
                    raise Exception(f'Could not unify {self} and {other}: cannot unify {arg1} and {arg2}')

        return Match(self.pred_name, new_args)

    def actual_args(self):
        actual_args = []
        for arg in self.pred_args:
            if type(arg) is VarRef:
                actual_args.append(arg.var_name)
            elif type(arg) is str:
                actual_args.append(arg)
            else:
                raise Exception("Argument '{}' is not: string or VarRef!".format(arg))
        return actual_args

    def call_with(self, pred_name, unification, rest_args):
        if self.match_any:
            raise Exception(f'Predicate not found: {pred_name}')
        i = 0
        final_args = []
        for arg in self.actual_args():
            if arg == 'any':
                if i >= len(rest_args):
                    # TODO: We should check this in the linter probably
                    raise Exception(f'Not enough arguments to call {self}: {rest_args}')

                final_args.append(rest_args[i])
                i += 1
            else:
                final_args.append(unification.get(arg, arg))

        return Call(self.pred_name, final_args)

    def __repr__(self):
        return '{}({})'.format(self.pred_name, ', '.join(map(repr, self.pred_args)))

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args if isinstance(args, list) else [args]

    def arity(self):
        return len(self.args)

    def match(self):
        return Match(self.name, self.args)

    def with_args(self, new_args):
        if len(new_args) == 0:
            return VarRef(self.name)
        else:
            return Call(self.name, new_args)

    def insert_first(self, new_arg):
        return Call(self.name, [new_arg] + self.actual_args())

    def actual_args(self):
        actual_args = []
        for arg in self.args:
            if type(arg) is VarRef:
                actual_args.append(arg.var_name)
            else:
                actual_args.append(arg)
        return actual_args

    def evaluate_node(self, prog):
        # We may need to compute some values for the args
        arg_preds = []
        final_args = []
        for arg in self.actual_args():
            # If it's not just a name, we need to actually do something
            if type(arg) is not str:
                new_var = prog.fresh_name()
                # For some reason we need to import again here?
                from pecan.lang.pecan_ast.arith import Equals
                arg_preds.append((Equals(arg, VarRef(new_var)), new_var))
                final_args.append(new_var)
            else:
                final_args.append(arg)

        from pecan.lang.pecan_ast.bool import Conjunction
        from pecan.lang.pecan_ast.quant import Exists

        final_pred = AutLiteral(prog.call(self.name, final_args))
        for pred, var_name in arg_preds:
            final_pred = Exists(var_name, Conjunction(pred, final_pred))

        return final_pred.evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Call(self)

    def __repr__(self):
        return '{}({})'.format(self.name, ', '.join(map(repr, self.args)))

class NamedPred(ASTNode):
    def __init__(self, name, args, body, restriction_env=None):
        super().__init__()
        self.name = name

        self.args = []
        self.arg_restrictions = []
        for arg in args:
            if type(arg) is VarRef:
                self.args.append(arg.var_name)
            elif type(arg) is str:
                self.args.append(arg)
            elif type(arg) is Call:
                self.args.append(arg.args[0])
                self.arg_restrictions.append(Restriction([arg.args[0]], arg.insert_first))
            else:
                raise Exception("Argument '{}' is not: string, VarRef, or a Call!".format(arg))

        self.restriction_env = restriction_env or {}

        self.body = body
        self.body_evaluated = None

    def evaluate(self, prog):
        # Here we keep track of all restrictions that were in scope when we are evaluated;
        # this essentially builds a closure. Otherwise, if we forget a variable after the declaration of this predicate,
        # then we will lose the restriction when we are called. This would cause our behavior to depend on lexically
        # where this predicate is used in the program, which would be confusing.
        prog.enter_scope()

        try:
            for arg_restriction in self.arg_restrictions:
                arg_restriction.evaluate(prog)

            self.restriction_env = prog.get_restriction_env()
        finally:
            prog.exit_scope()

    def transform(self, transformer):
        return transformer.transform_NamedPred(self)

    def arity(self):
        return len(self.args)

    def match(self):
        return Match(self.name, ['any'] * self.arity())

    def call(self, prog, arg_names=None):
        prog.enter_scope(dict(self.restriction_env))

        try:
            if self.body_evaluated is None:
                # We postprocess here because we will do it every time we call anyway (in AutomatonTransformer)
                self.body_evaluated = self.body.evaluate(prog) #.postprocess('BA')

            if arg_names is None:
                return self.body_evaluated
            else:
                subs_dict = {str(arg): spot.formula_ap(str(name)) for arg, name in zip(self.args, arg_names)}
                substitution = Substitution(subs_dict)
                return AutomatonTransformer(self.body_evaluated, substitution.substitute).transform()
        finally:
            prog.exit_scope()

    def __repr__(self):
        return '{}({}) := {}'.format(self.name, ', '.join(self.args), self.body)

class Program(ASTNode):
    def __init__(self, defs, *args, **kwargs):
        super().__init__()

        self.type_inferer = kwargs.get('type_inferer', None)
        self.defs = defs
        self.preds = kwargs.get('preds', {})
        self.context = kwargs.get('context', {})
        self.restrictions = kwargs.get('restrictions', [{}])
        self.types = kwargs.get('types', {})
        self.parser = kwargs.get('parser', None) # This will be "filled in" in the main.py after we load a program
        self.debug = kwargs.get('debug', 0)
        self.quiet = kwargs.get('quiet', False)
        self.eval_level = kwargs.get('eval_level', 0)
        self.result = kwargs.get('result', None)
        self.search_paths = kwargs.get('search_paths', [])
        self.fresh_counter = kwargs.get('fresh_counter', 0)

    def copy_defaults(self, other_prog):
        self.context = other_prog.context
        self.parser = other_prog.parser
        self.debug = other_prog.debug
        self.quiet = other_prog.quiet
        self.eval_level = other_prog.eval_level
        self.result = other_prog.result
        self.search_paths = other_prog.search_paths
        self.fresh_counter = other_prog.fresh_counter
        return self

    def include(self, other_prog):
        # Note: Intentionally do NOT merge restrictions, because it would be super confusing if variable restrictions "leaked" from imports
        self.preds.update(other_prog.preds)
        self.context.update(other_prog.context)
        self.types.update(other_prog.types)
        self.parser = other_prog.parser

        self.fresh_counter += other_prog.fresh_counter + 1

    def declare_type(self, pred_ref, val_dict):
        self.types[pred_ref] = val_dict

    def fresh_name(self):
        self.fresh_counter += 1
        # TODO: Merge this will the __pecan thing in ASTNode
        return f'__var{self.fresh_counter}'

    def evaluate(self, old_env=None):
        if old_env is not None:
            self.include(old_env)

        succeeded = True
        msgs = []

        for d in self.defs:
            if type(d) is NamedPred:
                # Infer types for the body of the
                self.preds[d.name] = self.type_inferer.reset().transform(d)
                self.preds[d.name].evaluate(self)
                if self.debug > 0:
                    print(self.preds[d.name])
            else:
                result = d.evaluate(self)
                if result is not None and type(result) is Result:
                    if result.failed():
                        succeeded = False
                        msgs.append(result.message())

        self.result = Result('\n'.join(msgs), succeeded)

        return self

    def transform(self, transformer):
        return transformer.transform_Program(self)

    def forget(self, var_name):
        self.restrictions[-1].pop(var_name)

    def restrict(self, var_name, pred):
        if pred is not None and pred not in self.get_restrictions(var_name):
            if type(pred) is not Call or len(pred.args) == 0:
                raise Exception('Unexpected predicate used as restriction (must be Call with the first argument as the variable to restrict): {}'.format(pred))

            if var_name in self.restrictions[-1]:
                self.restrictions[-1][var_name].append(pred)
            else:
                self.restrictions[-1][var_name] = [pred]

    def get_restriction_env(self):
        result = {}

        for restriction_set in self.restrictions:
            result.update(restriction_set)

        return result

    def enter_scope(self, new_restrictions=None):
        if new_restrictions is None:
            new_restrictions = {}
        self.restrictions.append(dict(new_restrictions))

    def exit_scope(self):
        if len(self.restrictions) <= 1:
            raise Exception('Cannot exit the last scope!')
        else:
            self.restrictions.pop(-1)

    def get_restrictions(self, var_name: str):
        result = []
        for scope in self.restrictions:
            for r in scope.get(var_name, []):
                if not r in result:
                    result.append(r)
        return result

    def call(self, pred_name, args=None):
        try:
            if args is None or len(args) == 0:
                if pred_name in self.preds:
                    return self.preds[pred_name].call(self, args)
                else:
                    raise Exception(f'Predicate {pred_name} not found (known predicates: {self.preds.keys()}!')
            else:
                return self.dynamic_call(pred_name, args)
        except Exception as e:
            if pred_name in self.context:
                return self.call(self.context[pred_name], args)
            else:
                raise e

    def unify_with(self, a, b, unification):
        if b in unification:
            return unification[b] == a
        else:
            unification[b] = a
            return True

    def unify_type(self, t1, t2, unification):
        if type(t1) is VarRef and type(t2) is VarRef:
            return self.unify_type(t1.var_name, t2.var_name, unification)
        elif type(t1) is str and type(t2) is str:
            return self.unify_with(t1, t2, unification)
        elif type(t1) is Call and type(t2) is Call:
            if t1.name != t2.name or len(t1.args) != len(t2.args):
                return False

            for arg1, arg2 in zip(t1.args, t2.args):
                if not self.unify_type(arg1, arg2, unification):
                    return False

            return True
        else:
            return False

    def try_unify_type(self, t1, t2, unification):
        old_unification = dict(unification)
        result = self.unify_type(t1, t2, unification)
        if result:
            return result
        else:
            # Do it this way so we mutate `unification` itself, and we don't want to change it unless we successfully unify
            unification.clear()
            unification.update(old_unification)
            return False

    def lookup_pred_by_name(self, pred_name):
        if pred_name in self.preds:
            return self.preds[pred_name]
        else:
            raise Exception(f'Predicate {pred_name} not found (known predicates: {self.preds.keys()}!')

    def lookup_call(self, pred_name, arg, unification):
        restrictions = self.get_restrictions(arg)

        # For now, use the restriction in the most local scope that we can find a match for
        # TODO: Improve this?
        for restriction in restrictions[::-1]:
            for t in self.types:
                if self.try_unify_type(restriction, t.insert_first(arg), unification):
                    if pred_name == restriction.name:
                        return restriction.match()
                    elif pred_name in self.types[t]:
                        return self.types[t][pred_name].match()
                    else:
                        return Match(match_any=True)

        return Match(match_any=True)

    # Dynamic dispatch based on argument types
    def dynamic_call(self, pred_name, args):
        matches = []
        unification = {}
        for arg in args:
            match = self.lookup_call(pred_name, arg, unification)
            if match is None:
                raise Exception(f'No matching predicate found for {arg} called {pred_name}')
            matches.append(match)

        # There will always be at least one match because there should always be
        # at least one argument, so no need for an initial value
        final_match = reduce(lambda a, b: a.unify(b), matches)

        # Match any means that we didn't find any type-specific matches
        if final_match.match_any:
            return self.lookup_pred_by_name(pred_name).call(self, args)
        else:
            final_call = final_match.call_with(pred_name, unification, args)
            return self.lookup_pred_by_name(final_call.name).call(self, final_call.args)

    def locate_file(self, filename):
        for path in self.search_paths:
            try_path = os.path.join(path, filename)
            if os.path.exists(try_path):
                return try_path

        raise FileNotFoundError(filename)

    def __repr__(self):
        return repr(self.defs)

class Result:
    def __init__(self, msg, succeeded):
        self.msg = msg
        self.__succeeded = succeeded

    def succeeded(self):
        return self.__succeeded

    def failed(self):
        return not self.succeeded()

    def message(self):
        return self.msg

    def print_result(self):
        if self.succeeded():
            print(f'{Fore.GREEN}{self.msg}{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}{self.msg}{Style.RESET_ALL}')


class Restriction(ASTNode):
    def __init__(self, var_names, pred):
        super().__init__()
        self.var_names = []
        for var_name in var_names if isinstance(var_names, list) else [var_names]:
            if type(var_name) is str:
                self.var_names.append(var_name)
            elif type(var_name) is VarRef:
                self.var_names.append(var_name.var_name)
            else:
                raise Exception("Argument '{}' is not a valid var name (string or VarRef)".format(var_name))
        self.pred = pred

    def evaluate(self, prog):
        for var_name in self.var_names:
            prog.restrict(var_name, self.pred(var_name))

    def transform(self, transformer):
        return transformer.transform_Restriction(self)

    def __repr__(self):
        return '{} are {}'.format(', '.join(self.var_names), self.pred('*')) # TODO: Improve this
