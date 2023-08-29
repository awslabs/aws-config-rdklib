import unittest
from unittest.mock import patch, MagicMock

import importlib

import sys
import os

# Get the absolute path of the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path of the project directory
project_dir = os.path.abspath(os.path.join(current_script_dir, "..", ".."))

# Add the project directory to the Python path
sys.path.append(project_dir)

CODE = importlib.import_module("rdklib.util.external")

CLIENT_FACTORY = MagicMock()
CLIENT_MOCK = MagicMock()


def mock_get_client(*args, **kwargs):
    return CLIENT_MOCK


def return_same_value(Evaluations, ResultToken, TestMode):
    return Evaluations


@patch.object(CLIENT_FACTORY, "build_client", MagicMock(side_effect=mock_get_client))
@patch.object(CLIENT_MOCK, "put_evaluations", MagicMock(side_effect=return_same_value))
class rdklibUtilExternalTest(unittest.TestCase):
    def test_external_process_evaluations(self):
        event_not_test = {"resultToken": "NOT_TESTMODE"}
        event_test = {"resultToken": "TESTMODE"}

        # No evaluation
        response = CODE.process_evaluations(event_test, CLIENT_FACTORY, [])
        self.assertEqual(response, [])

        # Evaluation in test mode
        response = CODE.process_evaluations(event_test, CLIENT_FACTORY, ["some-eval"])
        self.assertEqual(response, ["some-eval"])

        # Evaluation not in test mode
        response = CODE.process_evaluations(event_not_test, CLIENT_FACTORY, ["some-eval"])
        self.assertEqual(response, ["some-eval"])
