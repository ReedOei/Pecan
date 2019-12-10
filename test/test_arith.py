import unittest

import spot

from pecan.lang.parser import pecan_parser
from pecan.lang.ast import *

class ArithTest(unittest.TestCase):
    def print_addition(self):
        prop = "1+1=2"
        pred = pecan_parser.parse(prop)
        print(pred.evaluate(Program([])))

