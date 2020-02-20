import unittest
from mock import patch, MagicMock

CODE = __import__('external')

CLIENT_FACTORY = MagicMock()
CLIENT_MOCK = MagicMock()

def mock_get_client(*args, **kwargs):
    return CLIENT_MOCK

def return_same_value(Evaluations, ResultToken, TestMode):
    return Evaluations

@patch.object(CLIENT_FACTORY, 'build_client', MagicMock(side_effect=mock_get_client))
@patch.object(CLIENT_MOCK, 'put_evaluations', MagicMock(side_effect=return_same_value))
class rdklibUtilExternalTest(unittest.TestCase):

    def test_external_process_evaluations(self):
        event_not_test = {'resultToken': 'NOT_TESTMODE'}
        event_test = {'resultToken': 'TESTMODE'}

        # No evaluation
        response = CODE.process_evaluations(event_test, CLIENT_FACTORY, [])
        self.assertEqual(response, [])

        # Evaluation in test mode
        response = CODE.process_evaluations(event_test, CLIENT_FACTORY, ['some-eval'])
        self.assertEqual(response, ['some-eval'])

        # Evaluation not in test mode
        response = CODE.process_evaluations(event_not_test, CLIENT_FACTORY, ['some-eval'])
        self.assertEqual(response, ['some-eval'])
