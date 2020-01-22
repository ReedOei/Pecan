import unittest

from test.test_general import GeneralTest
from test.test_optimizer_tools import OptimizerToolsTest
from test.test_praline import PralineTest

def all_tests(test_classes):
    tests = []

    for test_class in test_classes:
        tests.extend(unittest.TestLoader().loadTestsFromTestCase(test_class))

    return unittest.TestSuite(tests)

if __name__ == '__main__':
    suite = all_tests([GeneralTest, OptimizerToolsTest, PralineTest])
    unittest.TextTestRunner(verbosity=2).run(suite)

