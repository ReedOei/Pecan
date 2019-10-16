#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style
import spot

from pecan.lang.pecan_ast.prog import *

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
        prog.call(self.pred_name).save(self.filename)
        return None

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

class DirectiveSaveAutImage(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        evaluated = prog.call(self.pred_name)
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

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(ASTNode):
    def __init__(self, truth_val, pred_name):
        super().__init__()
        self.truth_val = truth_val
        self.pred_name = pred_name

    def pred_truth_value(self, prog):
        evaluated = prog.call(self.pred_name)
        if evaluated.is_empty(): # If we accept nothing, we are false
            return 'false'
        elif spot.dualize(evaluated).is_empty(): # If our complement accepts nothing, we accept everything, so we are true
            return 'true'
        else: # Otherwise, we are neither true nor false: i.e., not all variables have been eliminated
            return 'sometimes'

    def evaluate(self, prog):
        pred_truth_value = self.pred_truth_value(prog)
        if pred_truth_value == self.truth_val:
            print(f'{Fore.GREEN}{self.pred_name} is {self.display_truth_val()}.{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}{self.pred_name} is not {self.display_truth_val()}.{Style.RESET_ALL}')

    def display_truth_val(self):
        if self.truth_val == 'sometimes':
            return 'sometimes true'
        else:
            return self.truth_val # 'true' or 'false'

    def __repr__(self):
        return '#assert_prop({}, {})'.format(self.truth_val, self.pred_name)

