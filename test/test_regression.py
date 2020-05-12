#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan import program
from pecan.settings import settings

def run_file(filename):
    orig_quiet = settings.is_quiet()
    settings.set_quiet(True)

    prog = program.load(filename)
    assert prog.evaluate().result.succeeded()

    settings.set_quiet(orig_quiet)

def test_free_var_regression0():
    run_file('examples/free-var-regression-0.pn')

def test_cse_loop_regression0():
    run_file('examples/cse-infinite-loop-regression0.pn')

