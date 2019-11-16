import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import *

PECAN_PATH_VAR = 'PECAN_PATH'

def make_search_paths():
    own_path = os.path.dirname(os.path.realpath(__file__))
    # Assuming we are in the test directory
    std_library_path = os.path.join(own_path, '..', 'library')
    automata_library_path = os.path.join(own_path, '..', 'library', 'automata')

    # Always include the current directory and the standard library folder
    search_paths = ['.', std_library_path, automata_library_path]

    if PECAN_PATH_VAR in os.environ:
        search_paths.extend(os.getenv(PECAN_PATH_VAR).split(os.pathsep))

    return search_paths

class QuantTest(unittest.TestCase):
    def run_file(self, filename):
        with open(filename, 'r') as f:
            prog = pecan_parser.parse(f.read())

        prog.parser = pecan_parser
        prog.search_paths = make_search_paths()
        prog.quiet = True

        self.assertTrue(prog.evaluate().result.succeeded())

    def test_load_pred(self):
        self.run_file('examples/load_aut.pn')

    def test_arith_basic(self):
        self.run_file('examples/test_arith.pn')

    def test_sturmian_basic(self):
        self.run_file('examples/test_sturmian.pn')

