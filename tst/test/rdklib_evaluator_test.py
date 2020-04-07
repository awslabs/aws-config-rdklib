import json
import unittest
from mock import patch, MagicMock
import botocore
from rdklib import InvalidParametersError

CODE = __import__('evaluator')

CLIENT_FACTORY = MagicMock()
CONFIG_CLIENT_MOCK = MagicMock()

def mock_get_client(client_name, *args, **kwargs):
    return CONFIG_CLIENT_MOCK

@patch.object(CLIENT_FACTORY, 'build_client', MagicMock(side_effect=mock_get_client))
@patch.object(CODE, 'check_defined', MagicMock(return_value=True))
class rdklibEvaluatorTest(unittest.TestCase):
    rule = MagicMock()

    def setUp(self):
        self.rule.reset_mock()

    def test_evaluator_init(self):
        evaluator = CODE.Evaluator('config-rule')
        self.assertEqual(evaluator.__dict__['_Evaluator__rdk_rule'], 'config-rule')
        self.assertEqual(evaluator.__dict__['_Evaluator__expected_resource_types'], [])
        
        applicable_resource_type = 'applicable-resource-type'
        evaluator = CODE.Evaluator('config-rule', [applicable_resource_type])
        self.assertEqual(evaluator.__dict__['_Evaluator__rdk_rule'], 'config-rule')
        self.assertEqual(evaluator.__dict__['_Evaluator__expected_resource_types'], [applicable_resource_type])

    def test_evaluator_handle_parameter_error(self):
        event = generate_event('some-msg-type')
        self.rule.evaluate_parameters.side_effect = InvalidParametersError('some-error')
        evaluator = CODE.Evaluator(self.rule)
        response = evaluator.handle(event, {})
        resp_expected = {'internalErrorMessage': 'Parameter value is invalid', 'internalErrorDetails': 'A ValueError was raised during the validation of the Parameter value', 'customerErrorMessage': 'some-error', 'customerErrorCode': 'InvalidParameterValueException'}
        self.assertDictEqual(response, resp_expected)

    def test_evaluator_handle_messagetype_error(self):
        event = generate_event('some-msg-type')
        self.rule.evaluate_parameters.return_value = 'some-param'
        evaluator = CODE.Evaluator(self.rule)
        response = evaluator.handle(event, {})
        resp_expected = {'internalErrorMessage': 'Unexpected message type', 'internalErrorDetails': "{'messageType': 'some-msg-type'}", 'customerErrorMessage': None, 'customerErrorCode': None}
        self.assertDictEqual(response, resp_expected)

    def test_evaluator_handle_boto_error(self):
        event = generate_event('ScheduledNotification')
        self.rule.evaluate_parameters.return_value = 'some-param'
        self.rule.evaluate_periodic.side_effect = botocore.exceptions.ClientError({'Error': {'Code': 'AccessDenied', 'Message': 'access-denied'}}, 'operation')
        evaluator = CODE.Evaluator(self.rule)
        response = evaluator.handle(event, {})
        resp_expected = {'internalErrorMessage': 'Insufficient access to perform this action.', 'internalErrorDetails': 'An error occurred (AccessDenied) when calling the operation operation: access-denied', 'customerErrorMessage': 'access-denied', 'customerErrorCode': 'AccessDenied'}
        self.assertDictEqual(response, resp_expected)

    def test_evaluator_handle_internal_error(self):
        event = generate_event('ScheduledNotification')
        self.rule.evaluate_parameters.return_value = 'some-param'
        self.rule.evaluate_periodic.side_effect = botocore.exceptions.ClientError({'Error': {'Code': 'InternalError', 'Message': 'some-internal-error'}}, 'operation')
        evaluator = CODE.Evaluator(self.rule)
        response = evaluator.handle(event, {})
        resp_expected = {'internalErrorMessage': 'Unexpected error while completing API request', 'internalErrorDetails': 'An error occurred (InternalError) when calling the operation operation: some-internal-error', 'customerErrorMessage': None, 'customerErrorCode': None}
        self.assertDictEqual(response, resp_expected)

    def test_evaluator_handle_other_error(self):
        event = generate_event('ScheduledNotification')
        self.rule.evaluate_parameters.return_value = 'some-param'
        self.rule.evaluate_periodic.side_effect = botocore.exceptions.ClientError({'Error': {'Code': 'OtherError', 'Message': 'some-other-error'}}, 'operation')
        evaluator = CODE.Evaluator(self.rule)
        response = evaluator.handle(event, {})
        resp_expected = {'internalErrorMessage': 'Customer error while making API request', 'internalErrorDetails': 'An error occurred (OtherError) when calling the operation operation: some-other-error', 'customerErrorMessage': 'some-other-error', 'customerErrorCode': 'OtherError'}
        self.assertDictEqual(response, resp_expected)

    def test_evaluator_handle_valueerror_error(self):
        event = generate_event('ScheduledNotification')
        rule = MagicMock()
        evaluator = CODE.Evaluator(rule)
        rule.evaluate_periodic.side_effect = ValueError('some-value-error')
        response = evaluator.handle(event, {})
        resp_expected = {'internalErrorMessage': 'some-value-error', 'internalErrorDetails': 'some-value-error', 'customerErrorMessage': None, 'customerErrorCode': None}
        self.assertDictEqual(response, resp_expected)

    @patch.object(CODE, 'process_periodic_evaluations_list', MagicMock(return_value=True))
    def test_evaluator_handle_schedule(self):
        rule = MagicMock()
        evaluator = CODE.Evaluator(rule)
        rule.evaluate_periodic.return_value = True
        event = generate_event('ScheduledNotification')
        response = evaluator.handle(event, {})
        self.assertTrue(response)

    @patch.object(CODE, 'process_event_evaluations_list', MagicMock(return_value=True))
    @patch.object(CODE, 'is_applicable_status', MagicMock(return_value=True))
    @patch.object(CODE, 'get_configuration_item', MagicMock(return_value=True))
    @patch.object(CODE, 'is_applicable_resource_type', MagicMock(return_value=True))
    def test_evaluator_handle_event_applicable(self):
        rule = MagicMock()
        evaluator = CODE.Evaluator(rule, ['resourceType'])
        rule.evaluate_change.return_value = True
        event = generate_event('ConfigurationItemChangeNotification')
        response = evaluator.handle(event, {})
        self.assertTrue(response)

    def test_evaluator_handle_event_change_triggered_no_expected_resources(self):
        rule = MagicMock()
        evaluator = CODE.Evaluator(rule, [])
        rule.evaluate_change.return_value = True
        event = generate_event('ConfigurationItemChangeNotification')

        with self.assertRaises(Exception) as context:
            evaluator.handle(event, {})
        self.assertTrue("Change triggered rules must provide expected resource types" in str(context.exception))

        evaluator = CODE.Evaluator(rule)
        with self.assertRaises(Exception) as context:
            evaluator.handle(event, {})
        self.assertTrue("Change triggered rules must provide expected resource types" in str(context.exception))

    @patch.object(CODE, 'process_event_evaluations_list', MagicMock(return_value=True))
    @patch.object(CODE, 'is_applicable_status', MagicMock(return_value=False))
    @patch.object(CODE, 'get_configuration_item', MagicMock(return_value=True))
    @patch.object(CODE, 'init_event', MagicMock(return_value={'messageType': 'OversizedConfigurationItemChangeNotification'}))
    def test_evaluator_handle_event_oversized_notapplicable(self):
        rule = MagicMock()
        evaluator = CODE.Evaluator(rule, ['resourceType'])
        event = generate_event('OversizedConfigurationItemChangeNotification')
        response = evaluator.handle(event, {})
        self.assertTrue(response)

    @patch.object(CODE, 'inflate_oversized_notification', MagicMock(return_value='some-notification'))
    def test_init_event(self):
        event = generate_event('some-msg-type')
        response = CODE.init_event(event, {})
        self.assertDictEqual(response, {'messageType':'some-msg-type'})

        event = generate_event('OversizedConfigurationItemChangeNotification')
        response = CODE.init_event(event, CLIENT_FACTORY)
        self.assertEqual(response, 'some-notification')

def generate_event(message_type):
    invoking_event = {'messageType': message_type};
    event = {
        'executionRoleArn': 'some-role-arn',
        'ruleParameters': json.dumps({'param_key': 'param_value'}).encode('utf8'),
        'accountId': 'accountId',
        'configRuleArn': 'ruleArn'
        }
    if message_type == 'ConfigurationItemChangeNotification':
        invoking_event.update({'configurationItem': generate_ci_data()})
    elif message_type == 'OversizedConfigurationItemChangeNotification':
        invoking_event.update({'configurationItemSummary': generate_ci_data()})
    event.update({'invokingEvent': json.dumps(invoking_event).encode('utf8')})
    return event

def generate_ci_data():
    return {'resourceType': 'resourceType', 'resourceId': 'resourceId', 'configurationStateId': 'configurationStateId'}
