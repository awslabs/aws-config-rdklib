# Copyright 2017-2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the License is located at
#
#        http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.

import boto3
import botocore
import os

CONFIG_ROLE_TIMEOUT_SECONDS = 900

class ClientFactory:
    __sts_credentials = None
    __role_arn = None
    __region = None
    __assume_role_mode = None

    def __init__(self, role_arn, region=None, assume_role_mode=True):
        self.__role_arn = role_arn
        self.__assume_role_mode = assume_role_mode
        if region == None:
            region = os.environ.get('AWS_REGION')
        self.__region = region

    def build_client(self, service, region=None, assume_role_mode=True):
        if not region:
            region = self.__region

        if not assume_role_mode:
            return boto3.client(service, region)
        elif not self.__assume_role_mode:
            return boto3.client(service, region)

        if not self.__role_arn:
            raise Exception("No Role ARN - ClientFactory must be initialized with a role_arn or set assume_role_mode to False before build_client is called. You can also add assume_role_arn mode to false in build_client() if you want to use the current iam role")
        
        # Check to see if we have already gotten STS credentials for this role.  If not, get them now and then save them for later use.
        if not self.__sts_credentials:
            self.__sts_credentials = get_assume_role_credentials(self.__role_arn, region)

        # Use the credentials to get a new boto3 client for the appropriate service.
        return boto3.client(service,
                            aws_access_key_id=self.__sts_credentials['AccessKeyId'],
                            aws_secret_access_key=self.__sts_credentials['SecretAccessKey'],
                            aws_session_token=self.__sts_credentials['SessionToken'],
                            region_name=region)

def get_assume_role_credentials(role_arn, region):
    try:
        try:
            #use region specific url for sts client is recommended. In some cases, company firewall policies are blocking the global endpoint sts.amazonaws.com
            assume_role_response = boto3.client('sts', region_name=region, endpoint_url="https://sts." + region + ".amazonaws.com").assume_role(RoleArn=role_arn,RoleSessionName="configLambdaExecution",DurationSeconds=CONFIG_ROLE_TIMEOUT_SECONDS)
        except:
            assume_role_response = boto3.client('sts').assume_role(RoleArn=role_arn,RoleSessionName="configLambdaExecution",DurationSeconds=CONFIG_ROLE_TIMEOUT_SECONDS)
        return assume_role_response['Credentials']
    except botocore.exceptions.ClientError as ex:
        if 'AccessDenied' in ex.response['Error']['Code']:
            ex.response['Error']['Message'] = "AWS Config does not have permission to assume the IAM role. Please try 1) grant the right priviledge to the assume the IAM role OR 2) provide Config Rules parameter \"EXECUTION_ROLE_NAME\" to specify a role to execute your rule OR 3)Set Config Rules parameter \"ASSUME_ROLE_MODE\" to False to use your lambda role instead of default Config Role."
        else:
            ex.response['Error']['Message'] = "InternalError"
            ex.response['Error']['Code'] = "InternalError"
        raise ex
