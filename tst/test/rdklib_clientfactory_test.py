import unittest
from unittest.mock import patch, MagicMock
import botocore

CODE = __import__('clientfactory')

STS_CLIENT_MOCK = MagicMock()
OTHER_CLIENT_MOCK = MagicMock()

def client(client_name, *args, **kwargs):
    if client_name == 'sts':
        return STS_CLIENT_MOCK
    return OTHER_CLIENT_MOCK

def credentials(role_arn):
    return {
        'AccessKeyId': 'some-key-id',
        'SecretAccessKey': 'some-secret',
        'SessionToken': 'some-token'
        }

@patch.object(CODE.boto3, 'client', MagicMock(side_effect=client))
class rdklibClientFactoryTest(unittest.TestCase):

    @patch.object(CODE, 'get_assume_role_credentials', MagicMock(side_effect=credentials))
    def test_clientfactory_build_client(self):
        # Init values
        client_factory = CODE.ClientFactory('arn:aws:iam:::role/some-role-name')
        self.assertEqual(client_factory.__dict__['_ClientFactory__role_arn'], 'arn:aws:iam:::role/some-role-name')

        # No role arn error
        client_factory.__dict__['_ClientFactory__role_arn'] = None
        with self.assertRaises(Exception) as context:
            client_factory.build_client('other')
        self.assertTrue('No Role ARN - ClientFactory must be initialized before build_client is called.' in str(context.exception))

        # No creds already
        client_factory.__dict__['_ClientFactory__role_arn'] = 'arn:aws:iam:::role/some-role-name'
        response = client_factory.build_client('other')
        self.assertEqual(response, OTHER_CLIENT_MOCK)

        # Creds already
        other_creds = {
            'AccessKeyId': 'some-other-key-id',
            'SecretAccessKey': 'some-other-secret',
            'SessionToken': 'some-other-token'
            }
        client_factory.__dict__['_ClientFactory__sts_credentials'] = other_creds
        client_factory.build_client('other')
        self.assertDictEqual(client_factory.__dict__['_ClientFactory__sts_credentials'], other_creds)

    def test_get_assume_role_credentials(self):
        STS_CLIENT_MOCK.assume_role.return_value = {'Credentials': 'some-creds'}
        response = CODE.get_assume_role_credentials('arn:aws:iam:::role/some-role-name')
        self.assertEqual(response, 'some-creds')

        STS_CLIENT_MOCK.assume_role.side_effect = botocore.exceptions.ClientError({'Error': {'Code': 'AccessDenied', 'Message': 'access-denied'}}, 'operation')
        with self.assertRaises(botocore.exceptions.ClientError) as context:
            CODE.get_assume_role_credentials('arn:aws:iam:::role/some-role-name')
        self.assertDictEqual(context.exception.response, {'Error': {'Code': 'AccessDenied', 'Message': 'AWS Config does not have permission to assume the IAM role.'}})

        STS_CLIENT_MOCK.assume_role.side_effect = botocore.exceptions.ClientError({'Error': {'Code': 'Some-other-error', 'Message': 'Some-other-error'}}, 'operation')
        with self.assertRaises(botocore.exceptions.ClientError) as context:
            CODE.get_assume_role_credentials('arn:aws:iam:::role/some-role-name')
        self.assertDictEqual(context.exception.response, {'Error': {'Code': 'InternalError', 'Message': 'InternalError'}})
