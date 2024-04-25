import importlib
import os
import sys
import unittest

# Get the absolute path of the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path of the project directory
project_dir = os.path.abspath(os.path.join(current_script_dir, "..", ".."))

# Add the project directory to the Python path
sys.path.append(project_dir)

CODE = importlib.import_module("rdklib.configrule")


class TEST_RULE_EMPTY(CODE.ConfigRule):
    pass


class TEST_RULE_CHANGED(CODE.ConfigRule):
    def evaluate_parameters(self, rule_parameters):
        return rule_parameters.strip()

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):
        return "COMPLIANT"

    def evaluate_change(self, event, client_factory, configuration_item, valid_rule_parameters):
        return "NON_COMPLIANT"

    def get_execution_role_arn(self, event):
        return "Some_ARN"


class rdklibConfigRuleTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_rule_default_behavior(self):
        my_empty_rule = TEST_RULE_EMPTY()
        with self.assertRaises(CODE.MissingTriggerHandlerError) as context:
            my_empty_rule.evaluate_periodic({}, {}, {})
        self.assertTrue(
            "You must implement the evaluate_periodic method of the ConfigRule class." in str(context.exception)
        )

        with self.assertRaises(CODE.MissingTriggerHandlerError) as context:
            my_empty_rule.evaluate_change({}, {}, {}, {})
        self.assertTrue(
            "You must implement the evaluate_change method of the ConfigRule class." in str(context.exception)
        )

        self.assertEqual("no_param", my_empty_rule.evaluate_parameters("no_param"))

        event_param_exec_role = {}
        event_param_exec_role["executionRoleArn"] = "aws:arn:account-and-stuff:role/some-role-path"
        self.assertEqual(
            event_param_exec_role["executionRoleArn"], my_empty_rule.get_execution_role_arn(event_param_exec_role)
        )

        event_param_exec_role = {}
        event_param_exec_role["executionRoleArn"] = "aws:arn:account-and-stuff:role/some-role-path"
        event_param_exec_role["ruleParameters"] = '{"some_param_key": "value"}'
        self.assertEqual(
            event_param_exec_role["executionRoleArn"], my_empty_rule.get_execution_role_arn(event_param_exec_role)
        )

        event_param_exec_role = {}
        event_param_exec_role["executionRoleArn"] = "aws:arn:account-and-stuff:role/some-role-path"
        event_param_exec_role["ruleParameters"] = '{"ExecutionRoleName": "some-role-name"}'
        expected_role_arn = "aws:arn:account-and-stuff:role/some-role-name"
        self.assertEqual(expected_role_arn, my_empty_rule.get_execution_role_arn(event_param_exec_role))

    def test_rule_methods_replaced(self):
        my_changed_rule = TEST_RULE_CHANGED()
        self.assertEqual("param", my_changed_rule.evaluate_parameters(" param "))
        self.assertEqual("COMPLIANT", my_changed_rule.evaluate_periodic({}, {}, {}))
        self.assertEqual("NON_COMPLIANT", my_changed_rule.evaluate_change({}, {}, {}, {}))
        self.assertEqual("Some_ARN", my_changed_rule.get_execution_role_arn({}))

    def test_get_assume_role_region(self):
        """The function: get_assume_role_region() should return appropriate value."""
        my_empty_rule = TEST_RULE_EMPTY()
        parameterized = [
            ({}, None),
            ({"ruleParameters": "{}"}, None),
            ({"ruleParameters": '{"ExecutionRoleRegion": "us-west-2"}'}, "us-west-2"),
        ]
        for event, expected in parameterized:
            with self.subTest(event):
                self.assertEqual(my_empty_rule.get_assume_role_region(event), expected)

    def test_get_assume_role_mode(self):
        """The function: get_assume_role_mode() should return appropriate value."""
        my_empty_rule = TEST_RULE_EMPTY()
        parameterized = [
            ({}, True),
            ({"ruleParameters": "{}"}, True),
            ({"ruleParameters": '{"AssumeRoleMode": "false"}'}, False),
            ({"ruleParameters": '{"AssumeRoleMode": "FALSE"}'}, False),
            ({"ruleParameters": '{"AssumeRoleMode": "true"}'}, True),
            ({"ruleParameters": '{"AssumeRoleMode": "TRUE"}'}, True),
        ]
        for event, expected in parameterized:
            with self.subTest(event):
                self.assertEqual(expected, my_empty_rule.get_assume_role_mode(event))
