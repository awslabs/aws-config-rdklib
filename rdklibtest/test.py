# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the License is located at
#
#        http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.

import json

############################
# Testing Helper Functions #
############################


def create_test_configurationchange_event(invoking_event_json, rule_parameters_json=None):
    event_to_return = {
        "configRuleName": "myrule",
        "executionRoleArn": "arn:aws:iam::123456789012:role/example",
        "eventLeftScope": False,
        "invokingEvent": json.dumps(invoking_event_json),
        "accountId": "123456789012",
        "configRuleArn": "arn:aws:config:us-east-1:123456789012:config-rule/config-rule-8fngan",
        "resultToken": "token",
    }
    if rule_parameters_json:
        event_to_return["ruleParameters"] = json.dumps(rule_parameters_json)
    return event_to_return


def create_test_scheduled_event(rule_parameters_json=None):
    invoking_event = {"messageType": "ScheduledNotification", "notificationCreationTime": "2017-12-23T22:11:18.158Z"}
    event_to_return = create_test_configurationchange_event(invoking_event, rule_parameters_json)
    return event_to_return


def assert_successful_evaluation(test_class, response, resp_expected, evaluations_count=1):
    test_class.assertEqual(len(response), len(resp_expected))
    test_class.assertEqual(len(response), evaluations_count)
    for i, response_expected in enumerate(resp_expected):
        test_class.assertEqual(response_expected, response[i])


def assert_customer_error_response(test_class, response, customer_error_code=None, customer_error_message=None):
    if customer_error_code:
        test_class.assertEqual(customer_error_code, response["customerErrorCode"])
    if customer_error_message:
        test_class.assertEqual(customer_error_message, response["customerErrorMessage"])
    test_class.assertTrue(response["customerErrorCode"])
    test_class.assertTrue(response["customerErrorMessage"])
    if "internalErrorMessage" in response:
        test_class.assertTrue(response["internalErrorMessage"])
    if "internalErrorDetails" in response:
        test_class.assertTrue(response["internalErrorDetails"])
