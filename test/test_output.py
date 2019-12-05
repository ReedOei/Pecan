import unittest

from contextlib import redirect_stdout
import io

from pecan import program

class GeneralTest(unittest.TestCase):
    def run_file(self, filename, expected_output):
        f = io.StringIO()
        with redirect_stdout(f):
            prog = program.load(filename, quiet=True)
            self.assertTrue(prog.evaluate().result.succeeded())
        self.assertEqual(f.getvalue().strip(), expected_output.strip())

    def test_show_word(self):
        self.run_file('examples/test_show_word.pn', '10010110011010010110100110010110011010011001011010010110011010010110100110010110100101100110100110010')

