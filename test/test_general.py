import unittest
from pecan import program
from pecan.settings import settings

class GeneralTest(unittest.TestCase):
    def run_file(self, filename):
        settings.set_quiet(True)
        prog = program.load(filename)
        self.assertTrue(prog.evaluate().result.succeeded())

    def test_load_pred(self):
        self.run_file('examples/test_load_aut.pn')

    def test_arith_basic(self):
        self.run_file('examples/test_arith.pn')

    def test_sturmian_basic(self):
        self.run_file('examples/test_sturmian.pn')

    def test_quant_file(self):
        self.run_file('examples/test_quant.pn')

    def test_stdlib_imported(self):
        self.run_file('examples/test_stdlib_imported.pn')

    def test_import_works(self):
        self.run_file('examples/test_import.pn')

    def test_quant_restricted(self):
        self.run_file('examples/test_quant_restricted.pn')

    def test_types(self):
        self.run_file('examples/test_types.pn')

    def test_restrict_is(self):
        self.run_file('examples/test_restrict_is.pn')

    def test_thue_morse(self):
        self.run_file('examples/thue_morse_props.pn')

    def test_word_indexing(self):
        self.run_file('examples/test_word_indexing.pn')

    def test_scope(self):
        self.run_file('examples/test_scope.pn')

    def test_chicken_mcnugget(self):
        self.run_file('examples/chicken_mcnugget.pn')

    def test_arith_props(self):
        self.run_file('examples/arith_props.pn')

    def test_fa19_poster_session(self):
        self.run_file('examples/fa19-poster-session.pn')

    def test_even(self):
        self.run_file('examples/test_even.pn')

    def test_word_syntax(self):
        self.run_file('examples/test_word_syntax.pn')

    def test_type_infer_arguments(self):
        self.run_file('examples/test_type_infer_arguments.pn')

    def test_function_expression(self):
        self.run_file('examples/test_function_expression.pn')

    def test_integers(self):
        self.run_file('examples/test_integers.pn')

    def test_real(self):
        self.run_file('examples/test_real.pn')

