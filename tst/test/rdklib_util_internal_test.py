import unittest

CODE = __import__('internal')

class rdklibUtilInternalTest(unittest.TestCase):

    def test_internal_process_evaluations(self):
        response = CODE.process_evaluations({}, {}, 'some-value')
        self.assertEqual(response, 'some-value')
