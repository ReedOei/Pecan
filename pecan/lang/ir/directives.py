#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import time

import buddy

from pecan.tools.shuffle_automata import ShuffleAutomata
from pecan.tools.walnut_converter import convert_aut
from pecan.tools.hoa_loader import load_hoa
from pecan.tools.labeled_aut_converter import convert_labeled_aut
from pecan.tools.hoa_loader import load_hoa
from pecan.tools.finite_loader import load_finite
from pecan.automata.buchi import BuchiAutomaton
from pecan.lang.ir import *

from pecan.settings import settings

class DirectiveSaveAut(IRNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def evaluate(self, prog):
        settings.log(lambda: f'[INFO] Saving {self.pred_name} as {self.filename}')

        prog.call(self.pred_name).save(self.filename)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAut(self)

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.filename == other.filename and self.pred_name == other.pred_name

    def __hash__(self):
        return hash((self.filename, self.pred_name))

class DirectiveSaveAutImage(IRNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def evaluate(self, prog):
        # TODO: Support formats other than SVG?
        settings.log(lambda: f'[INFO] Saving {self.pred_name} as an SVG in {self.filename}')

        evaluated = prog.call(self.pred_name)
        with open(self.filename, 'w') as f:
            f.write(evaluated.show().data) # Write the raw svg data into the file

        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAutImage(self)

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.filename == other.filename and self.pred_name == other.pred_name

    def __hash__(self):
        return hash((self.filename, self.pred_name))

class DirectiveContext(IRNode):
    def __init__(self, context_key, context_val):
        super().__init__()
        self.context_key = context_key
        self.context_val = context_val

    def evaluate(self, prog):
        prog.context[self.context_key] = self.context_val
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveContext(self)

    def __repr__(self):
        return '#context({}, {})'.format(self.context_key, self.context_val)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.context_key == other.context_key and self.context_val == other.context_val

    def __hash__(self):
        return hash((self.context_key, self.context_val))

class DirectiveEndContext(IRNode):
    def __init__(self, context_key):
        super().__init__()
        self.context_key = context_key

    def evaluate(self, prog):
        prog.context.pop(self.context_key)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveEndContext(self)

    def __repr__(self):
        return '#end_context({})'.format(self.context_key)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.context_key == other.context_key

    def __hash__(self):
        return hash(self.context_key)

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(IRNode):
    def __init__(self, truth_val, pred_name):
        super().__init__()
        self.truth_val = truth_val
        self.pred_name = pred_name

    def pred_truth_value(self, prog):
        return Call(self.pred_name, []).evaluate(prog).truth_value()

    def evaluate(self, prog):
        settings.log(lambda: f'[INFO] Checking if {self.pred_name} is {self.display_truth_val()}.')

        pred_truth_value = self.pred_truth_value(prog)

        if pred_truth_value == self.truth_val:
            result = Result(f'{self.pred_name} is {self.display_truth_val()}.', True)
        else:
            result = Result(f'{self.pred_name} is not {self.display_truth_val()}.', False)

        settings.log(lambda: result.result_str())

        return result

    def transform(self, transformer):
        return transformer.transform_DirectiveAssertProp(self)

    def display_truth_val(self):
        if self.truth_val == 'sometimes':
            return 'sometimes true'
        else:
            return self.truth_val # 'true' or 'false'

    def __repr__(self):
        return '#assert_prop({}, {})'.format(self.truth_val, self.pred_name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.truth_val == other.truth_val and self.pred_name == other.pred_name

    def __hash__(self):
        return hash((self.truth_val, self.pred_name))

class DirectiveLoadAut(IRNode):
    def __init__(self, filename, aut_format, pred):
        super().__init__()
        self.filename = filename
        self.aut_format = aut_format
        self.pred = pred

    def evaluate(self, prog):
        # TODO: Support argument restrictions on loaded automata
        start_time = time.time()
        realpath = prog.locate_file(self.filename)
        settings.log(lambda: f'[INFO] Loading {self.pred} from {realpath} in "{self.aut_format}" format.')

        if self.aut_format == 'hoa':
            # TODO: Rename the APs of the loaded automaton to be the same as the args specified
            aut = load_hoa(realpath)
        elif self.aut_format == 'walnut':
            aut = convert_aut(realpath, [v.var_name for v in self.pred.args])
        elif self.aut_format == 'pecan':
            aut = convert_labeled_aut(realpath, [v.var_name for v in self.pred.args])
        elif self.aut_format == 'fsa-dict':
            aut = load_finite(realpath, [v.var_name for v in self.pred.args])
        else:
            raise Exception('Unknown format: {}'.format(self.aut_format))

        end_time = time.time()

        settings.log(0, lambda: '[INFO] Loaded {} in {:.2f} seconds ({} states, {} edges).'.format(self.pred, end_time - start_time, aut.num_states(), aut.num_edges()))

        prog.preds[self.pred.name] = NamedPred(self.pred.name, self.pred.args, {}, AutLiteral(aut))

        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveLoadAut(self)

    def __repr__(self):
        return '#load({}, {}, {})'.format(self.filename, self.aut_format, repr(self.pred))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.filename == other.filename and self.aut_format == other.aut_format and self.pred == other.pred

    def __hash__(self):
        return hash((self.filename, self.aut_format, self.pred))

class DirectiveImport(IRNode):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def evaluate(self, prog):
        realpath = prog.locate_file(self.filename)
        from pecan.program import load
        new_prog = load(realpath).copy_defaults(prog)
        new_prog.evaluate()
        prog.include(new_prog)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveImport(self)

    def __repr__(self):
        return '#import({})'.format(repr(self.filename))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.filename == other.filename

    def __hash__(self):
        return hash(self.filename)

class DirectiveForget(IRNode):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def evaluate(self, prog):
        prog.forget_global(self.var_name)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveForget(self)

    def __repr__(self):
        return '#forget({})'.format(repr(self.var_name))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.var_name == other.var_name

    def __hash__(self):
        return hash(self.var_name)

class DirectiveStructure(IRNode):
    def __init__(self, pred_ref, val_dict):
        super().__init__()
        self.pred_ref = pred_ref
        self.val_dict = val_dict

    def evaluate(self, prog):
        prog.declare_type(self.pred_ref, self.val_dict)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveStructure(self)

    def __repr__(self):
        return 'Structure {} defining {}.'.format(self.pred_ref, self.val_dict)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.pred_ref == other.pred_ref and self.val_dict == other.val_dict

    def __hash__(self):
        return hash((self.pred_ref, self.val_dict))

class DirectiveShuffle(IRNode):
    def __init__(self, disjunction, pred_a, pred_b, output_pred):
        super().__init__()
        self.disjunction = disjunction
        self.pred_a = pred_a
        self.pred_b = pred_b
        self.output_pred = output_pred

    def transform(self, transformer):
        return transformer.transform_DirectiveShuffle(self)

    def evaluate(self, prog):
        # TODO: Support shuffling other kinds of automata, once we have them
        a_aut = BuchiAutomaton.as_buchi(prog.call(self.pred_a.name, self.pred_a.args))
        b_aut = BuchiAutomaton.as_buchi(prog.call(self.pred_b.name, self.pred_b.args))

        res = a_aut.shuffle(self.disjunction, b_aut)

        prog.preds[self.output_pred.name] = NamedPred(self.output_pred.name, self.output_pred.args, {}, AutLiteral(res))

        return None

    def __repr__(self):
        return '#shuffle({}, {}, {})'.format(self.pred_a, self.pred_b, self.output_pred)

class DirectivePlot(IRNode):
    def __init__(self, pred_name):
        super().__init__()
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectivePlot(self)

    # find the reachable states from the given initial states
    def find_reachable(self, buchi_aut, states):
        reachable = set(states)
        queue = list(states)
        while len(queue):
            state = queue.pop()
            for edge in buchi_aut.aut.out(state):
                # only follow satisfiable edges
                if edge.cond != buddy.bddfalse:
                    if edge.dst not in reachable:
                        reachable.add(edge.dst)
                        queue = [edge.dst] + queue
        return reachable

    """
    Given a buchi automata, checks if there exists an omega word
    accepted by it with the given prefix. Right now we only support
    a word on the alphabet { 0, ..., n - 1 }

    prefix should have the format "0120202", etc.
    """
    def accept_prefix(self, buchi_aut, prefix, n=3):
        twa = buchi_aut.aut

        # only support one argument case right now
        assert len(buchi_aut.var_map.items()) == 1, "#plot only support predicates with one free variable right now"

        # get bdd representations of each ap var
        # ap_names = buchi_aut.var_map.items[0][0]
        bdd_dict = twa.get_dict()
        bdds = [ buddy.bdd_ithvar(bdd_dict.varnum(ap_formula)) for ap_formula in twa.ap() ]

        # for bdd in bdds:
        #     print(bdd)

        # since the automata may be non-deterministic
        # keep a set of states
        current_states = { twa.state_number(twa.get_init_state()) }

        for letter in prefix:
            assert ord(letter) >= ord("0") and ord(letter) < ord("0") + n, "illegal letter in {}".format(prefix)

            assignment_bdd = buddy.bddtrue
            # TODO: check if the most significant bit corresponds to
            # the last item in the var_map lists
            for i, bdd in enumerate(bdds):
                # test if the ith bit is 1
                if int(letter) & (1 << (len(bdds) - i - 1)):
                    assignment_bdd = buddy.bdd_and(assignment_bdd, bdd)
                else:
                    assignment_bdd = buddy.bdd_and(assignment_bdd, buddy.bdd_not(bdd))

            # check all outgoing edges and update the current state set
            next_states = set()

            for state in current_states:
                for edge in twa.out(state):
                    # print(buddy.bdd_printset(edge.cond))
                    satisfiable = buddy.bdd_and(edge.cond, assignment_bdd) != buddy.bddfalse
                    # print(edge.cond, assignment_bdd, buddy.bdd_and(edge.cond, assignment_bdd))
                    if satisfiable:
                        next_states.add(edge.dst)

            # print(current_states, letter, next_states)

            current_states = next_states

        # TODO: we are assuming that all states are accepting
        # states (non-accepting ones should be removed from the
        # automata already)
        return len(current_states) != 0

        # # find all reachable states T1
        # # find all states reachable by T, T2
        # # take T = T1 /\ T2, which is the set of states
        # # that can be visited infinitely many times
        # t1 = self.find_reachable(buchi_aut, current_states)
        # t2 = self.find_reachable(buchi_aut, t1)
        # inf_set = t1.intersection(t2)

        # # checks if there is a satisfiable path from the current state to an accepting state
        # # twa.get_acceptance().used_sets()

        # # https://spot.lrde.epita.fr/doxygen/structspot_1_1acc__cond_1_1acc__code.html
        # # assuming acc_cond is of the form `Inf(i)`
        # acc_cond = twa.get_acceptance()
        # print(dir(acc_cond))
        # # print(spot.acc_cond.all_sets(acc_cond))

        # print(twa.get_acceptance())

        # print(current_states)

    def evaluate(self, prog):
        import matplotlib.pyplot as pt

        print("plotting {}".format(self.pred_name))
        buchi_aut = Call(self.pred_name, []).evaluate(prog)

        radix = 3

        for layer in range(10):
            total = radix ** layer
            for n in range(total):
                s = ""
                for i in range(layer):
                    s = str((n // (radix ** i)) % radix) + s

                possibly_acc = self.accept_prefix(buchi_aut, s, n=radix)

                # print(s, n, possibly_acc, total)
                length = 1 / total
                if possibly_acc:
                    pt.plot([n * length, n * length + length], [layer, layer], color="blue")

        # pt.savefig("")
        pt.show()

        # twa = buchi_aut.aut

        # print(buchi_aut.var_map)
        # print(twa.ap())
        # print(twa.get_dict().varnum(twa.ap()[0]))

        # # only support one argument case right now
        # # assert len(buchi_aut.var_map) == 1, "#plot only support predicates with one free variable right now"

        # # # get bdd representations of each ap var
        # # buchi_aut.var_map[0]

        # initial_state = twa.state_number(twa.get_init_state())
        # for edge in twa.out(initial_state):
        #     edge_cond = edge.cond

        #     print(edge.dst)

        #     ap1_bdd = buddy.bdd_ithvar(twa.get_dict().varnum(twa.ap()[0]))

        #     print(buddy.bdd_and(edge_cond, buddy.bdd_not(ap1_bdd)) == buddy.bddfalse)

        #     # buddy.bdd_apply()

    def __repr__(self):
        return '#plot({})'.format(self.pred_name)
