import math
import spot, buddy

# GLOBAL VARIABLES
state_counter = -1
states = dict()
org_states = []


# MISC HELPER FUNCTIONS
def first_word(string):
        fw = ""
        while len(string) and string[0] != ' ':
            fw += string[0]
            string = string[1:]
        string = string[1:]
        return (fw, string)

def column(l, c):
        column = ""
        for r in l:
            column += r[c]
        return column

def reset_global():
        global state_counter, states, org_states
        state_counter = -1
        states = dict()
        org_states = []


# STATE FUNCTIONS
def state_line(line):
        acc = line[-1]
        global org_states
        state(int(acc))
        org_states.append(str(state_counter))
        
def state(acc):
        state = {'acc': acc}
        global state_counter, states
        state_counter += 1
        states[str(state_counter)] = state


# EDGE FUNCTIONS
def intermediate_edge(b_inputs, start_state, end_state, base): 
        global states
        s = states[str(start_state)]
        for i in range(base):
            inp = column(b_inputs, i)
            if inp in s.keys():
                key = s[inp]
                if key[0] == 'o': 
                    key = org_states[int(key[1:])]
                    s[inp] = key
                s = states[key]
            elif i == base - 1:
                s[inp] = 'o' + str(end_state)
            else:
                new_state = state(0)
                name = str(state_counter)
                s[inp] = name
                s = states[name]

def edge(old_line, base):
        curr_inp = []
        while old_line[0] != '-':
            (inp, old_line) = first_word(old_line)
            curr_inp.append(('{0:b}'.format(int(inp))).zfill(base))
        end_state = old_line[3:].strip()
        intermediate_edge(curr_inp, org_states[-1], end_state, base)

def make_edge(aps, inp):
        ans = buddy.bddtrue
        for i in range(len(inp)):
            if inp[i] == '0':
                ans &= -aps[i]
            else:
                ans &= aps[i]
        return ans


# BASE FUNCTION 
def adjust_base(line):
        bases = []
        base = 1
        for c in line:
            if c == ',':
                base += 1
            elif c == '}':
                bases.append(base)
            elif c == '{':
                base = 1
        return bases


def convert_aut(txt, inp_names = []):
        reset_global()
        f = open(txt, 'r')

        bases = []
        base = 0

        for line in f.readlines():
            if line[0] == '{':
                bases = adjust_base(line)
                for i in range(len(bases)):
                    bases[i] = math.ceil(math.log(bases[i], 2))
                base = max(bases)
            elif '->' in line:
                edge(line.strip(), base)
            elif len(line) > 1:
                state_line(line.strip())
        f.close()

        aut = spot.make_twa_graph()
        aps = []
        for i in range(len(bases)):
            # should require same length? 
            if len(inp_names) > i:
                aps.append(buddy.bdd_ithvar(aut.register_ap(inp_names[i])))
            else: 
                aps.append(buddy.bdd_ithvar(aut.register_ap("p" + str(i + 1))))

        aut.set_buchi()
        aut.new_states(len(states))
        aut.set_init_state(0)

        for i in states:
            state = states[i]
            for j in state.keys():
                if j != "acc":
                    end_state = state[j]
                    if end_state[0] == 'o':
                        end_state = org_states[int(end_state[1:])]
                    end_state = end_state
                    label = make_edge(aps, j)
                    if states[end_state]["acc"]:
                        aut.new_edge(int(i), int(end_state), label, [0])
                    else: 
                        aut.new_edge(int(i), int(end_state), label)
        return aut
