import json
import unittest
from rdklib.evaluation import Evaluation, ComplianceType

import importlib

import sys
import os

# Get the absolute path of the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path of the project directory
project_dir = os.path.abspath(os.path.join(current_script_dir, "..", ".."))

# Add the project directory to the Python path
sys.path.append(project_dir)

CODE = importlib.import_module("rdklibtest.test")


class rdklibtestTest(unittest.TestCase):
    def test_assert_successful_evaluation(self):
        response = [Evaluation(ComplianceType.COMPLIANT, "some-resource-id", "some-resource-type", "some-annotation")]
        response_two = [
            Evaluation(ComplianceType.NON_COMPLIANT, "some-resource-id", "some-resource-type", "some-annotation")
        ]
        response_combine = response + response_two

        # AssertionError due to 2 different lenghts of response and resp_expected
        with self.assertRaises(AssertionError) as context:
            CODE.assert_successful_evaluation(self, response, response_combine)
        self.assertTrue("1 != 2" in str(context.exception))

        # AssertionError due to evaluation_count default
        with self.assertRaises(AssertionError) as context:
            CODE.assert_successful_evaluation(self, response_combine, response_combine)
        self.assertTrue("2 != 1" in str(context.exception))

        # AssertionError due to evaluation_count incorrect
        with self.assertRaises(AssertionError) as context:
            CODE.assert_successful_evaluation(self, response, response, 2)
        self.assertTrue("1 != 2" in str(context.exception))

        # Passing test for several evaluations
        CODE.assert_successful_evaluation(self, response, response)
        CODE.assert_successful_evaluation(self, response_combine, response_combine, 2)

    def test_assert_customer_error_response(self):
        error_message_no_code = {
            "internalErrorMessage": "some-internal-error-msg",
            "internalErrorDetails": "some-internal-error-details",
            "customerErrorCode": "",
        }
        error_message_no_msg = {
            "internalErrorMessage": "some-internal-error-msg",
            "internalErrorDetails": "some-internal-error-details",
            "customerErrorMessage": "",
            "customerErrorCode": "some-external-error-code",
        }
        error_message = {
            "internalErrorMessage": "some-internal-error-msg",
            "internalErrorDetails": "some-internal-error-details",
            "customerErrorMessage": "some-external-error-msg",
            "customerErrorCode": "some-external-error-code",
        }
        # Pass test
        CODE.assert_customer_error_response(self, error_message)

        # Customer code given
        CODE.assert_customer_error_response(self, error_message, "some-external-error-code")

        with self.assertRaises(AssertionError) as context:
            CODE.assert_customer_error_response(self, error_message, "some-code")
        self.assertTrue("'some-code' != 'some-external-error-code'" in str(context.exception))

        # Customer code not given, checking if present and not empty
        with self.assertRaises(AssertionError) as context:
            CODE.assert_customer_error_response(self, error_message_no_code)
        self.assertTrue("'' is not true" in str(context.exception))

        # Customer msg given
        CODE.assert_customer_error_response(self, error_message, customer_error_message="some-external-error-msg")

        with self.assertRaises(AssertionError) as context:
            CODE.assert_customer_error_response(self, error_message, customer_error_message="some-msg")
        self.assertTrue("'some-msg' != 'some-external-error-msg'" in str(context.exception))

        # Customer msg not given, checking if present and not empty
        with self.assertRaises(AssertionError) as context:
            CODE.assert_customer_error_response(self, error_message_no_msg)
        self.assertTrue("'' is not true" in str(context.exception))

        # Internal message, checking if not empty
        error_message_msg_empty = {
            "internalErrorMessage": "",
            "customerErrorMessage": "some-external-error-msg",
            "customerErrorCode": "some-external-error-code",
        }
        with self.assertRaises(AssertionError) as context:
            CODE.assert_customer_error_response(self, error_message_msg_empty)
        self.assertTrue("'' is not true" in str(context.exception))

        # Internal details, checking if not empty
        error_message_detail_empty = {
            "internalErrorMessage": "some-internal-error-msg",
            "internalErrorDetails": "",
            "customerErrorMessage": "some-external-error-msg",
            "customerErrorCode": "some-external-error-code",
        }
        with self.assertRaises(AssertionError) as context:
            CODE.assert_customer_error_response(self, error_message_detail_empty)
        self.assertTrue("'' is not true" in str(context.exception))

    def test_create_test_configurationchange_event(self):
        invoking_event = {"event": "my_event"}
        expected_event_no_param = {
            "configRuleName": "myrule",
            "executionRoleArn": "arn:aws:iam::123456789012:role/example",
            "eventLeftScope": False,
            "invokingEvent": '{"event": "my_event"}',
            "accountId": "123456789012",
            "configRuleArn": "arn:aws:config:us-east-1:123456789012:config-rule/config-rule-8fngan",
            "resultToken": "token",
        }
        self.assertDictEqual(CODE.create_test_configurationchange_event(invoking_event), expected_event_no_param)

        expected_event_param = {
            "configRuleName": "myrule",
            "executionRoleArn": "arn:aws:iam::123456789012:role/example",
            "eventLeftScope": False,
            "invokingEvent": '{"event": "my_event"}',
            "accountId": "123456789012",
            "configRuleArn": "arn:aws:config:us-east-1:123456789012:config-rule/config-rule-8fngan",
            "resultToken": "token",
            "ruleParameters": '{"somekeyparam": "somevalueparam"}',
        }
        parameter = {"somekeyparam": "somevalueparam"}
        self.assertDictEqual(
            CODE.create_test_configurationchange_event(invoking_event, parameter), expected_event_param
        )

    def test_create_test_scheduled_event(self):
        invoking_event = {
            "messageType": "ScheduledNotification",
            "notificationCreationTime": "2017-12-23T22:11:18.158Z",
        }

        expected_event_no_param = {
            "configRuleName": "myrule",
            "executionRoleArn": "arn:aws:iam::123456789012:role/example",
            "eventLeftScope": False,
            "invokingEvent": json.dumps(invoking_event),
            "accountId": "123456789012",
            "configRuleArn": "arn:aws:config:us-east-1:123456789012:config-rule/config-rule-8fngan",
            "resultToken": "token",
        }
        self.assertDictEqual(CODE.create_test_scheduled_event(), expected_event_no_param)

        expected_event_param = {
            "configRuleName": "myrule",
            "executionRoleArn": "arn:aws:iam::123456789012:role/example",
            "eventLeftScope": False,
            "invokingEvent": json.dumps(invoking_event),
            "accountId": "123456789012",
            "configRuleArn": "arn:aws:config:us-east-1:123456789012:config-rule/config-rule-8fngan",
            "resultToken": "token",
            "ruleParameters": '{"somekeyparam": "somevalueparam"}',
        }
        parameter = {"somekeyparam": "somevalueparam"}
        self.assertDictEqual(CODE.create_test_scheduled_event(parameter), expected_event_param)
