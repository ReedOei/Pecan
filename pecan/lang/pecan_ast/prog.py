#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from lark import Lark, Transformer, v_args

class ASTNode:
    id = 0
    def __init__(self):
        #TODO: detect used labels and avoid those
        self.label = "__pecan"+str(Expression.id)
        Expression.id += 1
        #TODO: remove this after it's done
        if prog.debug:
            print(self.label)
        pass

class Expression(ASTNode):
    def __init__(self):
        super().__init__()

    def evaluate(self, prog):
        return None

class BinaryExpression(ASTNode):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

class VarRef(Expression):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def evaluate(self, prog):
        # The automata accepts everything (because this isn't a predicate)
        return (spot.formula('1').translate(), self.var_name)

    def __repr__(self):
        return self.var_name

class Predicate(ASTNode):
    def __init__(self):
        super().__init__()

    # The evaluate function returns an automaton representing the expression
    def evaluate(self, prog):
        return None # Should never be called on the base Predicate class

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def __repr__(self):
        return '({}({}))'.format(self.name, ', '.join(self.args))

class NamedPred(ASTNode):
    def __init__(self, name, args, body):
        super().__init__()
        self.name = name
        self.args = args
        self.body = body

    def __repr__(self):
        return '{}({}) := {}'.format(self.name, ', '.join(self.args), self.body)

class Program(ASTNode):
    def __init__(self, defs):
        super().__init__()

        self.defs = defs
        self.preds = {}
        self.context = []
        self.parser = None # This will be "filled in" in the main.py after we load a program

    def evaluate(self, old_env=None):
        if old_env is not None:
            self.preds.update(old_env.preds)
            self.context = self.context + old_env.context
            self.parser = old_env.parser

        for d in self.defs:
            if type(d) is NamedPred:
                self.preds[d.name] = d
            else:
                d.evaluate(self)

        return self

    def __repr__(self):
        return repr(self.defs)

class Context:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '{}'.format(self.name)

class Directive(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return '#{}'.format(self.name)

class DirectiveSaveAut(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        prog.preds[self.pred_name].body.evaluate(prog).save(self.filename)
        return None

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

class DirectiveSaveAutImage(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        evaluated = prog.preds[self.pred_name].body.evaluate(prog)
        with open(self.filename, 'w') as f:
            f.write(evaluated.show().data) # Write the raw svg data into the file

        return None

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveSavePred(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        try:
            with open(self.filename, 'r') as f:
                new_prog = prog.parser.parse(f.read())

            with open(self.filename, 'w') as f:
                for d in new_prog.defs:
                    if type(d) is NamedPred and d.name == self.pred_name:
                        self.write_pred(f, prog)
                    else:
                        f.write(repr(d))
                        f.write('\n')
        except FileNotFoundError: # No problem, just create the file
            with open(self.filename, 'w') as f:
                self.write_pred(f, prog)


    def write_pred(self, f, prog):
        for ctx in prog.context:
            f.write(repr(DirectiveContext(ctx.name)))
            f.write('\n')
        f.write(repr(prog.preds[self.pred_name])) # Write the predicate definition itself into the file
        f.write('\n')
        for ctx in prog.context[::-1]:
            f.write(repr(DirectiveEndContext(ctx.name)))
            f.write('\n')

    def __repr__(self):
        return '#save_pred({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveLoadPreds(ASTNode):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename[1:-1]

    def evaluate(self, prog):
        with open(self.filename, 'r') as f:
            prog.parser.parse(f.read()).evaluate(prog)

        return None

    def __repr__(self):
        return '#load_preds({})'.format(repr(self.filename))

class DirectiveContext(ASTNode):
    def __init__(self, context_name):
        super().__init__()
        self.context = Context(context_name)

    def evaluate(self, prog):
        prog.context.append(self.context)
        return None

    def __repr__(self):
        return '#context({})'.format(self.context)

class DirectiveEndContext(ASTNode):
    def __init__(self, context_name):
        super().__init__()
        self.context = Context(context_name)

    def evaluate(self, prog):
        # Pop just the last context with this name
        rev_idx = prog.context[::-1].index(self.context)

        # TODO: Should we throw an error here if we don't find the context? Or just have a quick static checking phase at the beginning
        if rev_idx >= 0:
            prog.context.pop(len(prog.context) - rev_idx - 1) # Convert the index from an index in the reversed list to an index in the original list

        return None

    def __repr__(self):
        return '#end_context({})'.format(self.context)

