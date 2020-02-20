import unittest

CODE = __import__('configrule')

class TEST_RULE_EMPTY(CODE.ConfigRule):
    pass

class TEST_RULE_CHANGED(CODE.ConfigRule):
    def evaluate_parameters(self, rule_parameters):
        return rule_parameters.strip()

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):
        return "COMPLIANT"

    def evaluate_change(self, event, client_factory, configuration_item, valid_rule_parameters):
        return "NON_COMPLIANT"

class rdklibConfigRuleTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_rule_default_behavior(self):
        my_empty_rule = TEST_RULE_EMPTY()
        with self.assertRaises(CODE.MissingTriggerHandlerError) as context:
            my_empty_rule.evaluate_periodic({}, {}, {})
        self.assertTrue("You must implement the evaluate_periodic method of the ConfigRule class." in str(context.exception))

        with self.assertRaises(CODE.MissingTriggerHandlerError) as context:
            my_empty_rule.evaluate_change({}, {}, {}, {})
        self.assertTrue("You must implement the evaluate_change method of the ConfigRule class." in str(context.exception))

        self.assertEqual("no_param", my_empty_rule.evaluate_parameters("no_param"))

    def test_rule_methods_replaced(self):
        my_changed_rule = TEST_RULE_CHANGED()
        self.assertEqual("param", my_changed_rule.evaluate_parameters(" param "))
        self.assertEqual("COMPLIANT", my_changed_rule.evaluate_periodic({}, {}, {}))
        self.assertEqual("NON_COMPLIANT", my_changed_rule.evaluate_change({}, {}, {}, {}))
