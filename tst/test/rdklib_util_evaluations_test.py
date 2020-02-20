import json
import unittest
from mock import patch, MagicMock
from rdklib.configrule import ConfigRule
from rdklib.evaluation import ComplianceType, Evaluation

CODE = __import__('evaluations')

CLIENT_FACTORY = MagicMock()
CLIENT_MOCK = MagicMock()

def mock_get_client(*args, **kwargs):
    return CLIENT_MOCK

def return_same_value(event, client_factory, evaluations):
    return evaluations

def return_first_item(event, client_factory, evaluations):
    return evaluations[0]

@patch.object(CLIENT_FACTORY, 'build_client', MagicMock(side_effect=mock_get_client))
@patch.object(CODE, 'process_evaluations', MagicMock(side_effect=return_same_value))
class rdklibUtilEvaluationsTest(unittest.TestCase):

    event = {'invokingEvent': json.dumps({'notificationCreationTime': 'some-date-time'}), 'configRuleName': 'some-role-name'}

    def test_process_event_evaluations_list(self):

        eval_result = [Evaluation(ComplianceType.COMPLIANT, annotation='some-annotation')]
        eval_result_two = [Evaluation(ComplianceType.COMPLIANT)]
        eval_result_combine = eval_result + eval_result_two
        config_item = {
            'resourceType': 'some-resource-type',
            'resourceId': 'some-resource-id',
            'configurationItemCaptureTime': 'some-date-time'
            }

        # Empty evaluation list
        response = CODE.process_event_evaluations_list({}, {}, [], {})
        self.assertFalse(response)
        self.assertTrue(isinstance(response, list))

        # Invalid compliance results
        with self.assertRaises(Exception) as context:
            CODE.process_event_evaluations_list({}, {}, "string", {})
        self.assertTrue("The return statement from evaluate_change() is not a list." in str(context.exception))

        with self.assertRaises(Exception) as context:
            CODE.process_event_evaluations_list({}, {}, ["string", "string"], {})
        self.assertTrue("The return statement from evaluate_change() is not a list of Evaluation() object." in str(context.exception))

        # Valid compliance results with and without annotation
        response = CODE.process_event_evaluations_list({}, {}, eval_result_combine, config_item)
        resp_expected = [{'ComplianceResourceId': 'some-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'COMPLIANT', 'OrderingTimestamp': 'some-date-time', 'Annotation': 'some-annotation'}, {'ComplianceResourceId': 'some-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'COMPLIANT', 'OrderingTimestamp': 'some-date-time'}]
        for i, resp in enumerate(response):
            self.assertDictEqual(resp, resp_expected[i])

    @patch.object(CODE, 'clean_up_old_evaluations', MagicMock(side_effect=return_first_item))
    def test_process_periodic_evaluations_list(self):
        class SomeRuleClass(ConfigRule):
            pass
        rule = SomeRuleClass()
        rule.delete_old_evaluations_on_scheduled_notification = False

        eval_result = [Evaluation(ComplianceType.COMPLIANT)]
        eval_result_two = [Evaluation(ComplianceType.COMPLIANT, 'some-resource-id')]
        eval_result_three = [Evaluation(ComplianceType.COMPLIANT, 'some-resource-id', 'some-resource-type')]
        eval_result_four = [Evaluation(ComplianceType.NON_COMPLIANT, 'some-resource-id', 'some-resource-type', 'some-annotation')]
        eval_result_combine = eval_result_three + eval_result_four

        # Empty evaluation list
        response = CODE.process_periodic_evaluations_list({}, {}, [], rule)
        self.assertFalse(response)
        self.assertTrue(isinstance(response, list))

        # Invalid compliance results
        with self.assertRaises(Exception) as context:
            CODE.process_periodic_evaluations_list({}, {}, "string", rule)
        self.assertTrue("The return statement from evaluate_periodic() is not a list." in str(context.exception))

        with self.assertRaises(Exception) as context:
            CODE.process_periodic_evaluations_list({}, {}, ["string", "string"], rule)
        self.assertTrue("The return statement from evaluate_periodic() is not a list of Evaluation() object." in str(context.exception))

        # Missing information in evaluation
        with self.assertRaises(Exception) as context:
            CODE.process_periodic_evaluations_list(self.event, {}, eval_result, rule)
        self.assertTrue("Missing complianceResourceId from an evaluation result." in str(context.exception))

        with self.assertRaises(Exception) as context:
            CODE.process_periodic_evaluations_list(self.event, {}, eval_result_two, rule)
        self.assertTrue("Missing complianceResourceType from an evaluation result." in str(context.exception))

        # Valid compliance results with and without annotation
        response = CODE.process_periodic_evaluations_list(self.event, {}, eval_result_combine, rule)
        resp_expected = [{'ComplianceResourceId': 'some-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'COMPLIANT', 'OrderingTimestamp': 'some-date-time'}, {'ComplianceResourceId': 'some-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'NON_COMPLIANT', 'OrderingTimestamp': 'some-date-time', 'Annotation': 'some-annotation'}]
        for i, resp in enumerate(response):
            self.assertDictEqual(resp, resp_expected[i])

        # Test execution of clean_up_old_evaluations()
        rule.delete_old_evaluations_on_scheduled_notification = True
        response = CODE.process_periodic_evaluations_list(self.event, {}, eval_result_combine, rule)
        resp_expected = {'ComplianceResourceId': 'some-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'COMPLIANT', 'OrderingTimestamp': 'some-date-time'}
        self.assertDictEqual(response, resp_expected)

    def test_clean_up_old_evaluations(self):
        new_eval = [Evaluation(ComplianceType.COMPLIANT, 'some-resource-id', 'some-resource-type').get_json()]
        old_eval_overlapping = {'EvaluationResultIdentifier': {'EvaluationResultQualifier': {'ResourceId': 'some-resource-id', 'ResourceType': 'some-resource-type'}}}
        old_eval_not_overlapping = {'EvaluationResultIdentifier': {'EvaluationResultQualifier': {'ResourceId': 'some-other-resource-id', 'ResourceType': 'some-resource-type'}}}
        old_eval_list = [old_eval_overlapping, old_eval_not_overlapping]

        # Empty eval, empty old eval
        CLIENT_MOCK.get_compliance_details_by_config_rule.return_value = {'EvaluationResults':[]}
        response = CODE.clean_up_old_evaluations(self.event, CLIENT_FACTORY, [])
        self.assertFalse(response)
        self.assertTrue(isinstance(response, list))

        # Some eval, empty old eval
        CLIENT_MOCK.get_compliance_details_by_config_rule.return_value = {'EvaluationResults':[]}
        response = CODE.clean_up_old_evaluations(self.event, CLIENT_FACTORY, new_eval)
        resp_expected = {'ComplianceResourceId': 'some-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'COMPLIANT', 'OrderingTimestamp': None}
        self.assertDictEqual(response[0], resp_expected)

        # Some eval, Some old eval
        new_eval = [Evaluation(ComplianceType.COMPLIANT, 'some-resource-id', 'some-resource-type').get_json()]
        CLIENT_MOCK.get_compliance_details_by_config_rule.return_value = {'EvaluationResults': old_eval_list}
        response = CODE.clean_up_old_evaluations(self.event, CLIENT_FACTORY, new_eval)
        resp_expected = [{'ComplianceResourceId': 'some-other-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'NOT_APPLICABLE', 'OrderingTimestamp': 'some-date-time'}, {'ComplianceResourceId': 'some-resource-id', 'ComplianceResourceType': 'some-resource-type', 'ComplianceType': 'COMPLIANT', 'OrderingTimestamp': None}]
        for i, resp in enumerate(response):
            self.assertDictEqual(resp, resp_expected[i])
