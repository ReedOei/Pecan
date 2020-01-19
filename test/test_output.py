import unittest

from contextlib import redirect_stdout
import io

from pecan import program

class OutputTest(unittest.TestCase):
    def run_file(self, filename, expected_output):
        f = io.StringIO()
        with redirect_stdout(f):
            prog = program.load(filename, quiet=True)
            self.assertTrue(prog.evaluate().result.succeeded())
        self.assertEqual(f.getvalue().strip(), expected_output.strip())

    def test_accepting_word(self):
        self.run_file('examples/test_accepting_word.pn', '!x; !x; x; x; x; !x; x; cycle{!x}\nx: 0011101(0)^w')

