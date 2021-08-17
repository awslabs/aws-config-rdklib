import json
import unittest
from unittest.mock import patch, MagicMock
import botocore

CODE = __import__('service')
RESOURCE_TYPE = 'some-resource-type'

CONFIG_CLIENT_MOCK = MagicMock()

class rdklibUtilServiceTest(unittest.TestCase):

    def test_check_defined(self):
        ref = {}
        with self.assertRaises(Exception) as context:
            CODE.check_defined(ref, 'ref')
        self.assertTrue('Error: ref is not defined.' in str(context.exception))

        ref = {'key': 'value'}
        response = CODE.check_defined(ref, 'ref')
        self.assertEqual(response, ref)

    def test_is_applicable_status(self):
        status_false = ['ResourceDeleted', 'ResourceDeletedNotRecorded', 'ResourceNotRecorded']
        status_true = ['OK', 'ResourceDiscovered']

        for status in status_false:
            config_item = build_config_item(status)
            response = CODE.is_applicable_status(config_item, build_normal_event(False))
            self.assertFalse(response)
            response = CODE.is_applicable_status(config_item, build_normal_event(True))
            self.assertFalse(response)

        for status in status_true:
            config_item = build_config_item(status)
            response = CODE.is_applicable_status(config_item, build_normal_event(False))
            self.assertTrue(response)
            response = CODE.is_applicable_status(config_item, build_normal_event(True))
            self.assertFalse(response)

    def test_is_applicable_resource_type(self):
        config_item = build_config_item('OK')

        response = CODE.is_applicable_resource_type(config_item, ['other-resource-type'])
        self.assertFalse(response)

        response = CODE.is_applicable_resource_type(config_item, [RESOURCE_TYPE])
        self.assertTrue(response)

        response = CODE.is_applicable_resource_type(config_item, [])
        self.assertFalse(response)

    def test_get_configuration_item(self):
        invoke_event = {'configurationItem': 'some-ci'}
        response = CODE.get_configuration_item(invoke_event)
        self.assertEqual(response, 'some-ci')

    def test_is_internal_error(self):
        exception = Exception('some-error')
        response = CODE.is_internal_error(exception)
        self.assertTrue(response)

        exception = botocore.exceptions.ClientError({'Error': {'Code': '500'}}, 'operation')
        response = CODE.is_internal_error(exception)
        self.assertTrue(response)

        exception = botocore.exceptions.ClientError({'Error': {'Code': 'InternalError'}}, 'operation')
        response = CODE.is_internal_error(exception)
        self.assertTrue(response)

        exception = botocore.exceptions.ClientError({'Error': {'Code': 'ServiceError'}}, 'operation')
        response = CODE.is_internal_error(exception)
        self.assertTrue(response)

        exception = botocore.exceptions.ClientError({'Error': {'Code': '600'}}, 'operation')
        response = CODE.is_internal_error(exception)
        self.assertFalse(response)

        exception = botocore.exceptions.ClientError({'Error': {'Code': 'some-other-code'}}, 'operation')
        response = CODE.is_internal_error(exception)
        self.assertFalse(response)

    def test_build_error_response(self):
        response = CODE.build_error_response('int_msg', 'int_detail', 'ext_code', 'ext_msg')
        resp_expected = {
            'internalErrorMessage': 'int_msg',
            'internalErrorDetails': 'int_detail',
            'customerErrorMessage': 'ext_msg',
            'customerErrorCode': 'ext_code'
            }
        self.assertDictEqual(response, resp_expected)

    def test_build_internal_error_response(self):
        response = CODE.build_internal_error_response('int_msg', 'int_detail')
        resp_expected = {
            'internalErrorMessage': 'int_msg',
            'internalErrorDetails': 'int_detail',
            'customerErrorMessage': None,
            'customerErrorCode': None
            }
        self.assertDictEqual(response, resp_expected)

    def test_build_parameters_value_error_response(self):
        response = CODE.build_parameters_value_error_response('msg')
        resp_expected = {
            'internalErrorMessage': 'Parameter value is invalid',
            'internalErrorDetails': 'A ValueError was raised during the validation of the Parameter value',
            'customerErrorMessage': 'msg',
            'customerErrorCode': 'InvalidParameterValueException'
            }
        self.assertDictEqual(response, resp_expected)

    def test_is_oversized_changed_notification(self):
        message_type = 'OversizedConfigurationItemChangeNotification'
        response = CODE.is_oversized_changed_notification(message_type)
        self.assertTrue(response)

        message_type = 'other'
        response = CODE.is_oversized_changed_notification(message_type)
        self.assertFalse(response)

    def test_is_scheduled_notification(self):
        message_type = 'ScheduledNotification'
        response = CODE.is_scheduled_notification(message_type)
        self.assertTrue(response)

        message_type = 'other'
        response = CODE.is_scheduled_notification(message_type)
        self.assertFalse(response)

    def test_inflate_oversized_notification(self):
        CODE.get_resource_config_history = MagicMock(return_value=build_grh_response())
        CODE.convert_into_notification_config_item = MagicMock(return_value=build_config_item('some-type'))
        invoke_event = json.loads(build_normal_event(True)['invokingEvent'])
        response = CODE.inflate_oversized_notification({}, invoke_event)
        resp_expected = {'configurationItem': {'configurationItemStatus': 'some-type', 'resourceType': 'some-resource-type'}, 'notificationCreationTime': 'some-time', 'messageType': 'ConfigurationItemChangeNotification', 'recordVersion': 'some-version'}
        self.assertDictEqual(response, resp_expected)

    @patch.object(CONFIG_CLIENT_MOCK, 'get_resource_config_history', MagicMock(return_value='invoked'))
    def test_get_resource_config_history(self):
        invoke_event = json.loads(build_normal_event(True)['invokingEvent'])
        response = CODE.get_resource_config_history(CONFIG_CLIENT_MOCK, invoke_event)
        self.assertEqual(response, 'invoked')

    def test_convert_into_notification_config_item(self):
        response = CODE.convert_into_notification_config_item(build_grh_response()['configurationItems'][0])
        resp_expected = {'configurationItemCaptureTime': 'configurationItemCaptureTime', 'configurationStateId': 'configurationStateId', 'awsAccountId': 'accountId', 'configurationItemStatus': 'configurationItemStatus', 'resourceType': 'AWS::ResourceType', 'resourceId': 'resourceId', 'resourceName': 'resourceName', 'ARN': 'arn', 'awsRegion': 'awsRegion', 'availabilityZone': 'availabilityZone', 'configurationStateMd5Hash': 'configurationItemMD5Hash', 'resourceCreationTime': 'resourceCreationTime', 'relatedEvents': ['relatedEvent'], 'tags': {'tag': 'tag'}, 'relationships': [{'name': 'relationshipName', 'resourceId': 'resourceId', 'resourceName': 'resourceName', 'resourceType': 'resourceType'}], 'configuration': {'configuration': 'configuration'}, 'supplementaryConfiguration': {'supplementaryAttribute': {'supplementaryKey': 'supplementaryValue'}}}
        self.assertDictEqual(response, resp_expected)

def build_grh_response():
    return {
        'configurationItems': [
            {
                'version': 'version',
                'accountId': 'accountId',
                'configurationItemCaptureTime': 'configurationItemCaptureTime',
                'configurationItemStatus': 'configurationItemStatus',
                'configurationStateId': 'configurationStateId',
                'configurationItemMD5Hash': 'configurationItemMD5Hash',
                'arn': 'arn',
                'resourceType': 'AWS::ResourceType',
                'resourceId': 'resourceId',
                'resourceName': 'resourceName',
                'awsRegion': 'awsRegion',
                'availabilityZone': 'availabilityZone',
                'resourceCreationTime': 'resourceCreationTime',
                'tags': {
                    'tag': 'tag'
                },
                'relatedEvents': [
                    'relatedEvent',
                ],
                'relationships': [
                    {
                        'resourceType': 'resourceType',
                        'resourceId': 'resourceId',
                        'resourceName': 'resourceName',
                        'relationshipName': 'relationshipName'
                    },
                ],
                'configuration': '{"configuration": "configuration"}',
                'supplementaryConfiguration': {
                    'supplementaryAttribute': '{"supplementaryKey":"supplementaryValue"}'
                }
            }
        ]
    }

def build_config_item(message_type):
    return {
        'configurationItemStatus': message_type,
        'resourceType': RESOURCE_TYPE
        }

def build_normal_event(event_bool):
    return {
        'invokingEvent': json.dumps(
            {
                'configurationItemSummary': {
                    'resourceType': 'some-resource-type',
                    'resourceId': 'some-resource-id'
                    },
                'messageType': 'ConfigurationItemChangeNotification',
                'notificationCreationTime': 'some-time',
                'recordVersion': 'some-version',
                'configurationItem': {}
            }
        ),
        'executionRoleArn': 'roleArn',
        'eventLeftScope': event_bool
    }
