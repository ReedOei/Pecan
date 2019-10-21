import math

def first_word(string):
        fw = ""
        while len(string) and string[0] != ' ':
            fw += string[0]
            string = string[1:]
        string = string[1:]
        return (fw, string)

def state(old_line):
        new_line = 'State: '
        old_line = old_line[:len(old_line) - 1]
        (temp, old_line) = first_word(old_line) 
        new_line += temp
        return (new_line + ' { ' + first_word(old_line)[0] + ' }\n', temp)
        
def edge(old_line, bases):
        new_line = '['
        i = 0
        while old_line[0] != '-':
            (temp, old_line) = first_word(old_line) 
            if bases != []:
                binary = '0' + str(bases[i]) + 'b'
                i += 1
                temp = '&'.join([i for i in format(int(temp), binary)])
            new_line += temp + '&'
        new_line = new_line[:len(new_line) - 1] + '] '
        return new_line + old_line[3:]

def get_inputs(edge):
        counter = 0
        for l in edge:
            if l == '-':
                return counter
            if l != ' ':
                counter += 1
        # code shouldn't ever get here
        return counter

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

def convert_hoa(txt1, txt2):
        f1 = open(txt1, 'r')
        f2 = open(txt2, 'w')

        body = ['--BODY--\n']
        
        inputs = -1
        states = 0
        bases = []
        
        for line in f1.readlines():
            if line[0] == '{':
                bases = adjust_base(line)
                for i in range(len(bases)):
                    bases[i] = math.ceil(math.log(bases[i] + 1, 2))
            elif '->' in line:
                body.append(edge(line, bases))
                if inputs == -1:
                    inputs = get_inputs(line) 
            elif len(line) > 0:
                (temp, states) = state(line)
                body.append(temp)
        body.append('--END--')
        
        header = ['HOA: v1\n', 'States: ' + str(states) + '\n', 'acc-name: Buchi\n']
        header.append('Acceptance: 1 Inf(0)\n')
        
        aps = ''
        if bases != []:
            inputs = 0
            for base in bases:
                inputs += base
        for i in range(inputs):
            aps += ' "v' + str(i) + '"'
        header.append('AP: ' + str(inputs) + aps + '\n') 

        for line in (header + body):
            f2.write(line)
