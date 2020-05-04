#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from contextlib import redirect_stdout
import io

from pecan import program
from pecan.settings import settings

def run_file(filename, expected_output):
    orig = settings.is_quiet()
    settings.set_quiet(True)

    f = io.StringIO()
    with redirect_stdout(f):
        prog = program.load(filename)
        assert prog.evaluate().result.succeeded()
    assert f.getvalue().strip() == expected_output.strip()

    settings.set_quiet(orig_quiet)

def test_praline_simple():
    run_file('examples/test_praline_simple.pn', '1\n16\n')

def test_praline_list():
    run_file('examples/test_praline_list.pn', '[1,2,3,4]\n')

def test_praline_match():
    run_file('examples/test_praline_match.pn', '4\n[1,4,9,16]\n-49\n')

def test_praline_compose():
    run_file('examples/test_praline_compose.pn', '1\n0\n2\n')

def test_praline_builtins():
    run_file('examples/test_praline_builtins.pn', '7\n')

def test_praline_pecan_interop():
    run_file('examples/test_praline_pecan_interop.pn', 'false\ntrue\nfalse\n01101001100101101001011001101001100101100110100101101001100101101001011001101001011010011001011001101\n')

def test_praline_do():
    run_file('examples/test_praline_do.pn', '1\n2\n')

def test_praline_split():
    run_file('examples/test_praline_split.pn', '''
([1,2,3,4],[5,6,7,8,9,10])
[1,2,3,4]
[1,2,3,4,5,6,7,8,9,10]
''')

def test_praline_accepting_word():
    run_file('examples/test_praline_accepting_word.pn', '''
[(x,[([],[false])])]
[(x,[([false,false,true,true,true,false,true],[false])])]
''')

def test_praline_examples():
    run_file('examples/test_praline_examples.pn', '''
[(x,-2)]
''')

def test_praline_operators():
    run_file('examples/test_praline_operators.pn', '''
false
false
false
true
false
true
true
true
[true,false]
[true,true]
''')

def test_praline_graphing():
    run_file('examples/test_praline_graphing.pn', '''
[(-10,-20),(-9,-18),(-8,-16),(-7,-14),(-6,-12),(-5,-10),(-4,-8),(-3,-6),(-2,-4),(-1,-2),(0,0),(1,2),(2,4),(3,6),(4,8),(5,10),(6,12),(7,14),(8,16),(9,18),(10,20)]
''')

def test_praline_real_format():
    run_file('examples/test_praline_real_format.pn', '''
[(x,+1.0(0)^ω)]
[(y,+0.1(0)^ω)]
[(y,+11.10(10)^ω)]
''')

def test_praline_file_io():
    run_file('examples/test_praline_file_io.pn', '''
blah blah

''') # Note: the extra space is important. I want to test that we can write strings with newlines in them

def test_praline_split_on():
    run_file('examples/test_praline_split_on.pn', '''
[]
[[]]
[[],[1],[0,1],[0,0,0,1]]
''')

def test_praline_match_syntax():
    run_file('examples/test_praline_match_syntax.pn', '''
(8,10)
(88,83109)
''')

