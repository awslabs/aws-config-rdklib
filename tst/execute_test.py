import fnmatch
import os
import sys
import unittest

code_dir = "../rdklib"
code_dir_util = "../rdklib/util"
code_dir_test = "../rdklibtest"

sys.path.insert(0, code_dir)
sys.path.insert(0, code_dir_util)
sys.path.insert(0, code_dir_test)

test_dir = "../tst/test"

def create_test_suite():
    tests = []
    for root, _, filenames in os.walk(test_dir):
        for filename in fnmatch.filter(filenames, '*_test.py'):
            sys.path.append(root)
            tests.append(filename[:-3])
    suites = [unittest.defaultTestLoader.loadTestsFromName(test) for test in tests]
    return unittest.TestSuite(suites)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
results = unittest.TextTestRunner(buffer=True, verbosity=2).run(create_test_suite())

sys.exit(not results.wasSuccessful())