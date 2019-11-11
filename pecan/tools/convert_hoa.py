import math

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
        state_counter = 0
        states = dict()
        org_states = []


# STATE FUNCTIONS
def state_line(line):
        acc = line[-2]
        global org_states
        org_states.append(state_counter + 1)
        return state(acc)
        
def state(acc):
        line = 'State: '
        global state_counter, states
        state_counter += 1
        line += str(state_counter)
        if int(acc):
            line += ' {0}'
        line += '\n'
        state = {'print': line}
        states[str(state_counter)] = state
        return line


# EDGE FUNCTIONS
def intermediate_edge(b_inputs, start_state, end_state, base): 
        global states
        s = states[str(start_state)]
        for i in range(base):
            inp = column(b_inputs, i)
            if inp in s.keys():
                s = states[s[inp]]
            elif i == base - 1:
                s[inp] = 'o' + str(end_state)
            else:
                new_state = state('0')
                name = str(state_counter)
                s[inp] = name
                states[name] = {'print': new_state}
                s = states[name]

def edge(old_line, base):
        inputs = []
        while old_line[0] != '-':
            (inp, old_line) = first_word(old_line)
            inputs.append(('{0:b}'.format(int(inp))).zfill(base))
        end_state = old_line[3:-1]
        intermediate_edge(inputs, org_states[-1], end_state, base)

def print_edges(bin_str, state):
        return '[' + '&'.join(bin_str) + '] ' + str(state) + '\n'


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


# CONVERT FUNCTION
def convert_hoa(txt1, txt2):
        f1 = open(txt1, 'r')
        f2 = open(txt2, 'w')

        body = ['--BODY--\n']
        
        bases = []
        base = 0

        for line in f1.readlines():
            if line[0] == '{':
                bases = adjust_base(line)
                for i in range(len(bases)):
                    bases[i] = math.ceil(math.log(bases[i], 2))
                base = max(bases)
            elif '->' in line:
                edge(line, base)
            elif len(line) > 0:
                state_line(line)

        for i in states.keys():
            curr_state = states[i]
            body.append(curr_state['print'])
            del curr_state['print']
            for j in curr_state.keys():
                end_state = curr_state[j]
                if end_state[0] == 'o':
                    end_state = org_states[int(end_state[1:])]
                body.append(print_edges(j, end_state))

        body.append('--END--')

        global state_counter
        header = ['HOA: v1\n', 'States: ' + str(state_counter + 1) + '\n', 'acc-name: Buchi\n']
        header.append('Acceptance: 1 Inf(0)\n')
        
        aps = ''
        inputs = len(bases)
        for i in range(inputs):
            aps += ' "v' + str(i) + '"'
        header.append('AP: ' + str(inputs) + aps + '\n') 

        for line in (header + body):
            f2.write(line)
        
        reset_global()
