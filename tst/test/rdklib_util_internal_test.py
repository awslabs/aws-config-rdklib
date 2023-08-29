import unittest

import importlib

import sys
import os

# Get the absolute path of the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path of the project directory
project_dir = os.path.abspath(os.path.join(current_script_dir, "..", ".."))

# Add the project directory to the Python path
sys.path.append(project_dir)

CODE = importlib.import_module("rdklib.util.internal")


class rdklibUtilInternalTest(unittest.TestCase):
    def test_internal_process_evaluations(self):
        response = CODE.process_evaluations({}, {}, "some-value")
        self.assertEqual(response, "some-value")


if __name__ == "__main__":
    unittest.main()
