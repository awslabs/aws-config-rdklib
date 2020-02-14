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

from rdklib.evaluation import ComplianceType, Evaluation

try:
    from rdklib.util.internal import process_evaluations
except ImportError as ex:
    from rdklib.util.external import process_evaluations

# Build the evaluations list to return
def process_event_evaluations_list(event, client_factory, compliance_result, configuration_item):
    evaluations = []

    if not isinstance(compliance_result, list):
        print('The return statement from evaluate_change() is not a list.')
        raise Exception('The return statement from evaluate_change() is not a list.')

    for evaluation in compliance_result:
        if not isinstance(evaluation, Evaluation):
            print('The return statement from evaluate_change() is not a list of Evaluation() object.')
            raise Exception('The return statement from evaluate_change() is not a list of Evaluation() object.')
        evaluation.import_fields_from_configuration_item(configuration_item)
        if evaluation.is_valid():
            evaluations.append(evaluation.get_json())

    return process_evaluations(event, client_factory, evaluations)

def process_periodic_evaluations_list(event, client_factory, compliance_result, rule):
    evaluations = []
    latest_evaluations = []

    if not isinstance(compliance_result, list):
        print('The return statement from evaluate_periodic() is not a list.')
        raise Exception('The return statement from evaluate_periodic() is not a list.')

    for evaluation in compliance_result:
        if not isinstance(evaluation, Evaluation):
            print('The return statement from evaluate_periodic() is not a list of Evaluation() object.')
            raise Exception('The return statement from evaluate_periodic() is not a list of Evaluation() object.')
        evaluation.import_fields_from_periodic_event(event)
        if evaluation.is_valid():
            latest_evaluations.append(evaluation.get_json())

    if rule.delete_old_evaluations_on_scheduled_notification:
        evaluations = clean_up_old_evaluations(event, client_factory, latest_evaluations)
    else:
        evaluations = latest_evaluations

    return process_evaluations(event, client_factory, evaluations)

# This removes older evaluation (usually useful for periodic rule not reporting on AWS::::Account).
def clean_up_old_evaluations(event, client_factory, latest_evaluations):
    config_client = client_factory.build_client('config')
    latest_eval_ids = []
    for latest_eval in latest_evaluations:
        latest_eval_ids.append(latest_eval['ComplianceResourceId'])

    cleaned_evaluations = []

    old_evals = []
    next_token = ''
    while True:
        compliance_details = config_client.get_compliance_details_by_config_rule(
            ConfigRuleName=event['configRuleName'],
            ComplianceTypes=['COMPLIANT', 'NON_COMPLIANT'],
            Limit=100,
            NextToken=next_token)

        old_evals.extend(compliance_details['EvaluationResults'])
        next_token = compliance_details.get('nextToken', '')
        if not next_token:
            break

    for old_eval in old_evals:
        old_resource_id = old_eval['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceId']
        if old_resource_id not in latest_eval_ids:
            eval = Evaluation(
                        ComplianceType.NOT_APPLICABLE,
                        old_resource_id,
                        resourceType=old_eval['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceType']
                    )
            eval.import_fields_from_periodic_event(event)

            cleaned_evaluations.append(
                eval.get_json()
            )

    return cleaned_evaluations + latest_evaluations
