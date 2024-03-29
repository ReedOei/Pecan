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

def test_praline_define_aut():
    run_file('examples/test_praline_define_aut.pn')

def test_load_pred():
    run_file('examples/test_load_aut.pn')

def test_arith_basic():
    run_file('examples/test_arith.pn')

def test_sturmian_basic():
    run_file('examples/test_sturmian.pn')

def test_quant_file():
    run_file('examples/test_quant.pn')

def test_stdlib_imported():
    run_file('examples/test_stdlib_imported.pn')

def test_import_works():
    run_file('examples/test_import.pn')

def test_quant_restricted():
    run_file('examples/test_quant_restricted.pn')

def test_types():
    run_file('examples/test_types.pn')

def test_restrict_is():
    run_file('examples/test_restrict_is.pn')

def test_thue_morse():
    run_file('examples/thue_morse_props.pn')

def test_word_indexing():
    run_file('examples/test_word_indexing.pn')

def test_scope():
    run_file('examples/test_scope.pn')

def test_chicken_mcnugget():
    run_file('examples/chicken_mcnugget.pn')

def test_arith_props():
    run_file('examples/arith_props.pn')

def test_fa19_poster_session():
    run_file('examples/fa19-poster-session.pn')

def test_even():
    run_file('examples/test_even.pn')

def test_word_syntax():
    run_file('examples/test_word_syntax.pn')

def test_type_infer_arguments():
    run_file('examples/test_type_infer_arguments.pn')

def test_function_expression():
    run_file('examples/test_function_expression.pn')

def test_integers():
    run_file('examples/test_integers.pn')

def test_real():
    run_file('examples/test_real.pn')

# def test_zeckendorf():
#     run_file('examples/test_zeckendorf.pn')

def test_bounded_ostrowski_2():
    run_file('examples/test_bounded_ostrowski_2.pn')

def test_parse_not_precedence():
    run_file('examples/test_parse_not_precedence.pn')

def test_quant_multiple_vars():
    run_file('examples/test_quant_multiple_vars.pn')

def test_annotations():
    run_file('examples/test_annotations.pn')

def test_thue_morse_periods():
    run_file('examples/thue_morse_periods.pn')

def test_min_function():
    run_file('examples/test_min_function.pn')

def test_max_function():
    run_file('examples/test_max_function.pn')

def test_inf_function():
    run_file('examples/test_inf_function.pn')

def test_sup_function():
    run_file('examples/test_sup_function.pn')

def test_finite_basics():
    run_file('examples/test_finite_aut.pn')

def test_constraints():
    run_file('examples/test_constraints.pn')

def test_div():
    run_file('examples/test_div.pn')

def test_website():
    run_file('examples/website_tests.pn')

def test_praline_constant_mul():
    run_file('examples/praline_constant_mul.pn')

def test_fractal():
    # NOTE: This isn't a correctness test so much as it is a "this shouldn't crash test."
    # TODO: Add some correctness testing for fractals
    run_file('examples/fractal.pn')

