# Copyright 2017-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import botocore
from rdklib.util.evaluations import process_event_evaluations_list, process_periodic_evaluations_list
from rdklib.util.service import build_parameters_value_error_response, build_internal_error_response, build_error_response, is_applicable, is_internal_error, check_defined, get_configuration_item, inflate_oversized_notification
from rdklib.clientfactory import ClientFactory
from rdklib.evaluation import ComplianceType, Evaluation
from rdklib.errors import InvalidParametersError

class Evaluator:
    __rdk_rule = None

    def __init__(self, config_rule):
        self.__rdk_rule = config_rule

    def handle(self, event, context):

        check_defined(event, 'event')

        client_factory = ClientFactory(self.__rdk_rule.get_execution_role_arn(event))
        invoking_event = init_event(event, client_factory)

        rule_parameters = {}
        if 'ruleParameters' in event:
            rule_parameters = json.loads(event['ruleParameters'])

        try:
            valid_rule_parameters = self.__rdk_rule.evaluate_parameters(rule_parameters)
        except InvalidParametersError as ex:
            return build_parameters_value_error_response(ex)

        try:
            if invoking_event['messageType'] == 'ScheduledNotification':
                compliance_result = self.__rdk_rule.evaluate_periodic(event, client_factory, valid_rule_parameters)
                return process_periodic_evaluations_list(event, client_factory, compliance_result, self.__rdk_rule)
            if invoking_event['messageType'] in ['ConfigurationItemChangeNotification', 'OversizedConfigurationItemChangeNotification']:
                configuration_item = get_configuration_item(invoking_event)
                if is_applicable(configuration_item, event):
                    compliance_result = self.__rdk_rule.evaluate_change(event, client_factory, configuration_item, valid_rule_parameters)
                else:
                    compliance_result = [Evaluation(ComplianceType.NOT_APPLICABLE)]
                return process_event_evaluations_list(event, client_factory, compliance_result, configuration_item)
            return build_internal_error_response('Unexpected message type', str(invoking_event))
        except botocore.exceptions.ClientError as ex:
            if is_internal_error(ex):
                return build_internal_error_response("Unexpected error while completing API request", str(ex))
            return build_error_response("Customer error while making API request", str(ex), ex.response['Error']['Code'], ex.response['Error']['Message'])
        except ValueError as ex:
            return build_internal_error_response(str(ex), str(ex))

def init_event(event, client_factory):
    invoking_event = json.loads(event['invokingEvent'])
    if not invoking_event['messageType'] == 'OversizedConfigurationItemChangeNotification':
        return invoking_event

    # TODO: move to batch GRH
    config_client = client_factory.build_client('config')
    change_notification = inflate_oversized_notification(config_client, invoking_event)
    return change_notification
