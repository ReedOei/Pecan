import spot
import buddy

import lark

"""
omega-regular expression syntax

s := "rs" | "s|s" | "sω" | "(s)"

r := <ap> | "r1|r2" | "r1r2" | "r1*" | "(r)"
"""

class OREBase:
    def __repr__(self):
        return str(self)

    def get_atoms(self):
        raise NotImplementedError()

    def construct_automaton(self, bdict):
        raise NotImplementedError()

    # copy all states and transitions
    # from the old automaton to the new automaton
    # and return a mapping of states
    def copy_states(self, new, old):
        new.copy_ap_of(old)
        state_map = {}

        for i in range(old.num_states()):
            new_state = new.new_state()
            state_map[i] = new_state

        for i in range(old.num_states()):
            for edge in old.out(i):
                new.new_edge(state_map[i], state_map[edge.dst], edge.cond)

        return state_map

    def merge_automata(self, left, right):
        assert left.get_dict() == right.get_dict()
        new = spot.make_twa_graph(left.get_dict())

        left_state_map = self.copy_states(new, left)
        right_state_map = self.copy_states(new, right)

        return new, left_state_map, right_state_map


class OREAtom(OREBase):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return f"{self.name}"

    def get_atoms(self):
        return {self.name}

    def construct_automaton(self, bdict):
        aut = spot.make_twa_graph(bdict)
        ap = buddy.bdd_ithvar(aut.register_ap(self.name))
        st1 = aut.new_state()
        st2 = aut.new_state()
        aut.new_edge(st1, st2, ap)
        return aut, st1, {st2}


# including both the regular Kleene closure and ω
class OREKleene(OREBase):
    def __init__(self, base):
        self.base = base

    def __str__(self):
        return f"({self.base})*"

    def get_atoms(self):
        return self.base.get_atoms()

    def construct_automaton(self, bdict):
        base_aut, start_state, accepting_states = self.base.construct_automaton(bdict)

        for start_state_out in base_aut.out(start_state):
            for accepting_state in accepting_states:
                base_aut.new_edge(accepting_state, start_state_out.dst, start_state_out.cond)

        return base_aut, start_state, accepting_states


class OREConcat(OREBase):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({self.left})({self.right})"

    def get_atoms(self):
        return self.left.get_atoms().union(self.right.get_atoms())

    def construct_automaton(self, bdict):
        left_aut, left_start_state, left_accepting_states = self.left.construct_automaton(bdict)
        right_aut, right_start_state, right_accepting_states = self.right.construct_automaton(bdict)

        new_aut, left_state_map, right_state_map = self.merge_automata(left_aut, right_aut)

        # connect the left accepting states to the right start state
        for right_start_out in right_aut.out(right_start_state):
            for left_accepting_state in left_accepting_states:
                new_aut.new_edge(left_state_map[left_accepting_state], right_state_map[right_start_out.dst], right_start_out.cond)

        return new_aut, left_state_map[left_start_state], [ right_state_map[state] for state in right_accepting_states ]


class OREUnion(OREBase):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({self.left})|({self.right})"

    def get_atoms(self):
        return self.left.get_atoms().union(self.right.get_atoms())

    def construct_automaton(self, bdict):
        left_aut, left_start_state, left_accepting_states = self.left.construct_automaton(bdict)
        right_aut, right_start_state, right_accepting_states = self.right.construct_automaton(bdict)

        new_aut, left_state_map, right_state_map = self.merge_automata(left_aut, right_aut)

        new_start_state = new_aut.new_state()

        for left_start_state_out in new_aut.out(left_state_map[left_start_state]):
            new_aut.new_edge(new_start_state, left_start_state_out.dst, left_start_state_out.cond)

        for right_start_state_out in new_aut.out(right_state_map[right_start_state]):
            new_aut.new_edge(new_start_state, right_start_state_out.dst, right_start_state_out.cond)

        new_accepting_states = [ left_state_map[state] for state in left_accepting_states ] + \
                               [ right_state_map[state] for state in right_accepting_states ]

        return new_aut, new_start_state, new_accepting_states


class OmegaRegularExpressionTransformer(lark.Transformer):
    def ap(self, arg):
        return OREAtom(arg[0].value)

    def primary(self, arg):
        return arg[0]

    def kleene(self, arg):
        return OREKleene(arg[0])

    def concat(self, arg):
        left, right = arg
        return OREConcat(left, right)

    def union(self, arg):
        left, right = arg
        return OREUnion(left, right)

    def regex(self, arg):
        return arg[0]


parser = lark.Lark("""
AP: /[^()*ω|]/

primary: AP             -> ap
       | "(" regex ")"
       | primary "*"    -> kleene

concat: primary         -> primary
      | concat primary  -> concat

regex: concat
     | regex "|" concat -> union

omega: regex "ω"        -> kleene
     | regex omega      -> concat
     | omega "|" omega  -> union
""", start="omega", parser="lalr", transformer=OmegaRegularExpressionTransformer())

expr = parser.parse(r"(a*b|c)ω")
print(expr, expr.get_atoms())

bdict = spot.make_bdd_dict()
aut = spot.make_twa_graph(bdict)
aut, start_state, accepting_states = expr.construct_automaton(bdict)
aut = spot.simplify(aut)
print(start_state)
print(accepting_states)
print(aut.to_str("hoa"))
exit()

bdict = spot.make_bdd_dict()
aut = spot.make_twa_graph(bdict)
var_map = {}

a = buddy.bdd_ithvar(aut.register_ap("a"))
b = buddy.bdd_ithvar(aut.register_ap("b"))

# aut.set_generalized_buchi(2)
aut.set_acceptance(1, "Inf(1)")

aut.new_states(2)
# The default initial state is 0, but it is always better to
# specify it explicitly.
aut.set_init_state(0)

# new_edge() takes 3 mandatory parameters: source state, destination state,
# and label.  A last optional parameter can be used to specify membership to
# acceptance sets.  In the Python version, the list of acceptance sets the
# transition belongs to should be specified as a list.
# aut.new_edge(0, 1, p1)
# aut.new_edge(1, 1, p1 & p2, [0])
# aut.new_edge(1, 2, p2, [1])
# aut.new_edge(2, 1, p1 | p2, [0, 1])

aut.new_edge(0, 0, a)
aut.new_edge(0, 1, buddy.bddtrue)
aut.new_edge(1, 1, buddy.bddtrue, [1])

print(aut.to_str('hoa'))

print(spot.product)

print(aut.accepting_word())
