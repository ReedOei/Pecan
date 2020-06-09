#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import os
from functools import reduce
import time

from lark import Lark, Transformer, v_args
import spot

from pecan.automata.automaton import FalseAutomaton
from pecan.tools.hoa_loader import from_spot_aut
from pecan.lang.ir.base import *
from pecan.settings import settings
from pecan.utility import VarMap

class VarRef(IRExpression):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name
        self.is_int = False

    def evaluate(self, prog):
        # The automata accepts everything (because this isn't a predicate)
        from pecan.lang.ir.bool import BoolConst
        return BoolConst(True).evaluate(prog), self

    def transform(self, transformer):
        return transformer.transform_VarRef(self)

    def show(self):
        return str(self.var_name)

    def __repr__(self):
        return self.show()

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var_name == other.var_name and self.get_type() == other.get_type()

    def __hash__(self):
        return hash((self.var_name, self.get_type()))

class AutLiteral(IRPredicate):
    def __init__(self, aut, display_node=None):
        super().__init__()
        self.aut = aut
        self.is_int = False
        self.display_node = display_node

    def evaluate(self, prog):
        return self.aut

    def transform(self, transformer):
        return transformer.transform_AutLiteral(self)

    def show(self):
        return repr(self)

    def __repr__(self):
        if self.display_node is not None:
            return 'AutLiteral({})'.format(repr(self.display_node))
        else:
            return 'AUTOMATON LITERAL'

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.aut == other.aut

    def __hash__(self):
        return hash((self.aut))

class SpotFormula(IRPredicate):
    def __init__(self, formula_str):
        super().__init__()
        self.formula_str = formula_str

    def evaluate(self, prog):
        try:
            return from_spot_aut(spot.translate(self.formula_str))
        except:
            return from_spot_aut(spot.parse_word(self.formula_str).as_automaton())

    def transform(self, transformer):
        return transformer.transform_SpotFormula(self)

    def __repr__(self):
        return 'LTL({})'.format(self.formula_str)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.formula_str == other.formula_str

    def __hash__(self):
        return hash((self.formula_str))

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

    def call_with(self, pred_name, unification, rest_args):
        if self.match_any:
            raise Exception(f'Predicate not found: {pred_name}')
        i = 0
        final_args = []
        for arg in self.pred_args:
            if arg.var_name == 'any':
                if i >= len(rest_args):
                    # TODO: We should check this in the linter probably
                    raise Exception(f'Not enough arguments to call {self}: {rest_args}')

                final_args.append(rest_args[i])
                i += 1
            else:
                final_args.append(VarRef(unification.get(arg.var_name, arg.var_name)))

        return Call(self.pred_name, final_args)

    def __repr__(self):
        return '{}({})'.format(self.pred_name, ', '.join(map(repr, self.pred_args)))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.pred_name == other.pred_name and self.pred_args == other.pred_args and self.match_any == other.match_any

    def __hash__(self):
        return hash((self.pred_name, self.pred_args, self.match_any))

class Call(IRPredicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def arity(self):
        return len(self.args)

    def match(self):
        return Match(self.name, self.args)

    def with_args(self, new_args):
        return Call(self.name, new_args)

    def add_arg(self, new_arg):
        return Call(self.name, self.args + [new_arg]).with_type(self.get_type())

    def subs_last(self, new_arg):
        return self.with_args(self.args[:-1] + [new_arg]).with_type(self.get_type())

    def evaluate_node(self, prog):
        return prog.call(self.name, self.args)

    def transform(self, transformer):
        return transformer.transform_Call(self)

    def __repr__(self):
        return '{}({})'.format(self.name, ', '.join(map(repr, self.args)))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.name == other.name and self.args == other.args

    def __hash__(self):
        return hash((self.name, tuple(self.args)))

class NamedPred(IRNode):
    def __init__(self, name, args, arg_restrictions, body, restriction_env=None, body_evaluated=None, arg_name_map=None):
        super().__init__()
        self.name = name

        self.args = args
        self.arg_restrictions = arg_restrictions
        self.body = body

        self.restriction_env = restriction_env or {}
        self.body_evaluated = body_evaluated
        self.arg_name_map = arg_name_map or {}

    def evaluate(self, prog):
        # Here we keep track of all restrictions that were in scope when we are evaluated;
        # this essentially builds a closure. Otherwise, if we forget a variable after the declaration of this predicate,
        # then we will lose the restriction when we are called. This would cause our behavior to depend on lexically
        # where this predicate is used in the program, which would be confusing.
        prog.enter_scope()

        try:
            for _, arg_restriction in self.arg_restrictions.items():
                arg_restriction.evaluate(prog)

            self.restriction_env = prog.get_restriction_env()

            from pecan.lang.optimizer.tools import FreeVars
            free_vars = FreeVars().analyze(self.body)
            diff = free_vars - set(arg.var_name for arg in self.args)
            if len(diff) > 0:
                settings.log(lambda: "[WARN] Free variables found in {}: {}".format(self.name, diff))
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
                self.body_evaluated = self.body.evaluate(prog).relabel()

            if not arg_names:
                return self.body_evaluated
            else:
                if len(arg_names) < len(self.args):
                    raise Exception('Not enough arugments for {}. Expected {}, got {}'.format(self.name, len(self.args), len(arg_names)))
                subs_dict = {arg.var_name: name.var_name for arg, name in zip(self.args, arg_names)}
                return self.body_evaluated.substitute(subs_dict, prog.get_var_map())
        finally:
            prog.exit_scope()

    def __repr__(self):
        if self.body_evaluated is None:
            return '{}({}) := {}'.format(self.name, ', '.join(map(repr, self.args)), self.body)
        else:
            return '{}({}) := {} (evaluated)'.format(self.name, ', '.join(map(repr, self.args)), self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.name == other.name and self.args == other.args and self.arg_restrictions == other.arg_restrictions and self.body == other.body and self.restriction_env == other.restriction_env

    def __hash__(self):
        return hash((self.name, tuple(self.args)))

class Program(IRNode):
    def __init__(self, defs, *args, **kwargs):
        super().__init__()

        self.defs = defs
        self.preds = kwargs.get('preds', {})
        self.context = kwargs.get('context', {})
        self.restrictions = kwargs.get('restrictions', [{}])
        self.global_restrictions = kwargs.get('global_restrictions', {})
        self.types = kwargs.get('types', {})
        self.eval_level = kwargs.get('eval_level', 0)
        self.result = kwargs.get('result', None)
        self.search_paths = kwargs.get('search_paths', [])

        self.praline_envs = kwargs.get('praline_envs', [])
        self.praline_defs = kwargs.get('praline_defs', {})
        self.praline_aliases = kwargs.get('praline_aliases', {})

        # The current to-process index in self.defs
        # This is used for emitting new definitions via Praline (see Program.emit_definition and pecan.lib.praline.builtins.Emit)
        self.idx = None
        self.emit_offset = 0

        self.var_map = []

        from pecan.lang.type_inference import TypeInferer
        self.type_inferer = TypeInferer(self)

    def get_var_map(self):
        return self.var_map[-1]

    def enter_praline_env(self, new_env=None):
        if new_env is None:
            self.praline_envs.append({})
        else:
            self.praline_envs.append(new_env)

    def exit_praline_env(self):
        return self.praline_envs.pop()

    def praline_lookup(self, name):
        if name in self.praline_envs[-1]:
            return self.praline_envs[-1][name]

        if name in self.praline_defs:
            return self.praline_defs[name]

        if name in self.preds:
            from pecan.lang.ir.praline import PralineString
            return PralineString(name)

        raise Exception('Unknown symbol: "{}"'.format(name))

    def praline_env_clone(self):
        return dict(self.praline_envs[-1])

    def define_alias(self, name, alias):
        self.praline_aliases[name] = alias

    def lookup_alias(self, name):
        if name in self.praline_aliases:
            return self.praline_aliases[name]
        else:
            raise Exception('Unknown alias name: {}'.format(name))

    def praline_define(self, name, val):
        self.praline_defs[name] = val

    def praline_local_define(self, name, val):
        self.praline_envs[-1][name] = val

    def praline_local_define_all(self, env):
        self.praline_envs[-1].update(env)

    def praline_local_cleanup(self, names):
        for name in names:
            self.praline_envs[-1].pop(name)

    def copy_defaults(self, other_prog):
        self.context = other_prog.context
        self.eval_level = other_prog.eval_level
        self.result = other_prog.result
        self.search_paths.extend(other_prog.search_paths)
        return self

    def include(self, other_prog):
        # Note: Intentionally do NOT merge restrictions, because it would be super confusing if variable restrictions "leaked" from imports
        self.preds.update(other_prog.preds)
        self.context.update(other_prog.context)
        self.types.update(other_prog.types)

        self.praline_defs.update(other_prog.praline_defs)
        self.praline_aliases.update(other_prog.praline_aliases)

    def include_with_restrictions(self, other_prog):
        self.include(other_prog)

        self.global_restrictions.update(other_prog.global_restrictions)

    def declare_type(self, pred_ref, val_dict):
        self.types[pred_ref] = val_dict

    def type_infer(self, node):
        return self.type_inferer.reset().transform(node)

    def emit_definition(self, d):
        self.emit_offset += 1
        self.defs.insert(self.idx + self.emit_offset, d)
        self.run_definition(self.idx + self.emit_offset, d)

    def run_definition(self, i, d):
        from pecan.lang.typed_ir_lowering import TypedIRLowering
        from pecan.lang.optimizer.optimizer import UntypedOptimizer, Optimizer

        if isinstance(d, NamedPred):
            settings.log(1, lambda: '[DEBUG] Type inference and IR lowering for: {}'.format(d.name))
            transformed_def = TypedIRLowering(self).transform(self.type_infer(d))

            if settings.opt_enabled():
                settings.log(1, lambda: '[DEBUG] Performing typed optimization on: {}'.format(d.name))
                transformed_def = Optimizer(self).optimize(transformed_def)

            transformed_def = TypedIRLowering(self).transform(transformed_def)
            settings.log(1, lambda: 'Lowered IR:')
            settings.log(1, lambda: transformed_def)

            self.defs[i] = transformed_def
            self.preds[d.name] = self.defs[i]
            self.preds[d.name].evaluate(self)
            settings.log(0, lambda: self.preds[d.name])
        else:
            return d.evaluate(self)

    def evaluate(self, old_env=None):
        from pecan.lib.praline.builtins import builtins

        for builtin in builtins:
            builtin.evaluate(self)

        if old_env is not None:
            self.include(old_env)

        succeeded = True
        msgs = []
        self.idx = 0

        # Don't use a for, because Praline code can insert new definitions dynamically
        while self.idx < len(self.defs):
            self.enter_var_map_scope()

            self.emit_offset = 0
            d = self.defs[self.idx]

            settings.log(0, lambda: '[DEBUG] Processing: {}'.format(d))
            result = self.run_definition(self.idx, d)
            if result is not None and type(result) is Result:
                if result.failed():
                    succeeded = False
                    msgs.append(result.message())

            self.idx += 1 + self.emit_offset

            self.exit_var_map_scope()

        # Clear all restrictions. All relevant restrictions will be held inside the restriction_env of the relevant predicates.
        # Having them also in our restrictions list just leads to double restricting, which is a waste of computation time
        self.restrictions.clear()
        self.idx = None

        self.result = Result('\n'.join(msgs), succeeded)

        return self

    def transform(self, transformer):
        return transformer.transform_Program(self)

    def forget(self, var_name):
        self.restrictions[-1].pop(var_name)

    def forget_global(self, var_name):
        self.global_restrictions.pop(var_name)

    def global_restrict(self, var_name, pred):
        if pred is not None and pred not in self.get_restrictions(var_name):
            if type(pred) is not Call or not pred.args:
                raise Exception('Unexpected predicate used as restriction (must be Call with the first argument as the variable to restrict): {}'.format(pred))

            if var_name in self.global_restrictions:
                self.global_restrictions[var_name].append(pred)
            else:
                self.global_restrictions[var_name] = [pred]

    def restrict(self, var_name, pred):
        if pred is not None and pred not in self.get_restrictions(var_name):
            if type(pred) is not Call or not pred.args:
                raise Exception('Unexpected predicate used as restriction (must be Call with the first argument as the variable to restrict): {}'.format(pred))

            if var_name in self.restrictions[-1]:
                self.restrictions[-1][var_name].append(pred)
            else:
                self.restrictions[-1][var_name] = [pred]

    def get_restriction_env(self):
        result = {}
        result.update(self.global_restrictions)
        result.update(self.restrictions[-1])

        return result

    def enter_scope(self, new_restrictions=None):
        if new_restrictions is None:
            new_restrictions = {}
        self.restrictions.append(dict(new_restrictions))

    def exit_scope(self):
        if self.restrictions:
            self.restrictions.pop(-1)
        else:
            raise Exception('Cannot exit the last scope!')

    def enter_var_map_scope(self, var_map=None):
        self.var_map.append(var_map or VarMap())

    def exit_var_map_scope(self):
        return self.var_map.pop()

    def get_restrictions(self, var_name: str):
        result = []
        # for scope in self.restrictions:
        for r in self.restrictions[-1].get(var_name, []) + self.global_restrictions.get(var_name, []):
            if not r in result:
                result.append(r)
        return result

    def call(self, pred_name, args=None):
        try:
            if not args:
                if pred_name in self.preds:
                    return self.preds[pred_name].call(self, args)
                else:
                    raise Exception(f'Predicate {pred_name}({args}) not found (known predicates: {self.preds.keys()}!')
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
            return self.unify_with(t1.var_name, t2.var_name, unification)
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
        if arg.get_type() is None:
            return Match(match_any=True)

        for t in self.types:
            restriction = arg.get_type().restrict(arg)
            if self.try_unify_type(restriction, t.restrict(arg), unification):
                if pred_name in self.types[t]:
                    return self.types[t][pred_name].match()
                else:
                    return Match(match_any=True)

        return Match(match_any=True)

    def lookup_dynamic_call(self, pred_name, args):
        matches = []
        unification = {}
        for arg in args:
            match = self.lookup_call(pred_name, arg, unification)
            if match is None:
                raise Exception(f'No matching predicate found for {arg} called {pred_name}')
            matches.append(match)

        # There will always be at least one match because there should always be
        # at least one argument, so no need for an initial value
        final_match = reduce(lambda a, b: a.unify(b), matches, Match(match_any=True))

        # Match any means that we didn't find any type-specific matches
        if final_match.match_any:
            return Call(pred_name, args)
        else:
            return final_match.call_with(pred_name, unification, args)

    # Dynamic dispatch based on argument types
    def dynamic_call(self, pred_name, args):
        final_call = self.lookup_dynamic_call(pred_name, args)
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

    def result_str(self):
        if self.succeeded():
            return f'{Fore.GREEN}{self.msg}{Style.RESET_ALL}'
        else:
            return f'{Fore.RED}{self.msg}{Style.RESET_ALL}'

class Restriction(IRNode):
    def __init__(self, restrict_vars, pred):
        super().__init__()
        self.restrict_vars = restrict_vars
        self.pred = pred

    def evaluate(self, prog):
        for var in self.restrict_vars:
            prog.global_restrict(var.var_name, self.pred.add_arg(var))

    def transform(self, transformer):
        return transformer.transform_Restriction(self)

    def __repr__(self):
        return 'Restrict {} are {}.'.format(', '.join(map(repr, self.restrict_vars)), self.pred)

