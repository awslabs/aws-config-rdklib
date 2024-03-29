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

import json

class ConfigRule:
    #Set this to True to prevent removal of old evaluations when evaluate_compliance returns a list of compliance results.
    delete_old_evaluations_on_scheduled_notification = True

    def __init__(self):
        pass

    def evaluate_parameters(self, rule_parameters):
        return rule_parameters

    def evaluate_change(self, event, client_factory, configuration_item, valid_rule_parameters):
        raise MissingTriggerHandlerError("You must implement the evaluate_change method of the ConfigRule class.")

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):
        raise MissingTriggerHandlerError("You must implement the evaluate_periodic method of the ConfigRule class.")

    def get_execution_role_arn(self, event):
        role_arn = None
        if 'ruleParameters' in event:
            rule_params = json.loads(event['ruleParameters'])
            role_name = rule_params.get("ExecutionRoleName")
            if role_name:
                execution_role_prefix = event["executionRoleArn"].split("/")[0]
                role_arn = "{}/{}".format(execution_role_prefix, role_name)

        if not role_arn:
            role_arn = event['executionRoleArn']

        return role_arn

    def get_assume_role_region(self, event):
        assume_role_region = None
        if 'ruleParameters' in event:
            rule_params = json.loads(event['ruleParameters'])
            assume_role_region = rule_params.get("ExecutionRoleRegion")

        return assume_role_region
    
    def get_assume_role_mode(self, event):
        assume_role_mode = True
        if 'ruleParameters' in event:
            rule_params = json.loads(event['ruleParameters'])
            if "AssumeRoleMode" in rule_params:
                assume_role_mode = rule_params.get("AssumeRoleMode").lower() != "false"

        return assume_role_mode

class MissingTriggerHandlerError(Exception):
    pass
