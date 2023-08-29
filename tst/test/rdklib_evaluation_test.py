import json
import unittest

# from rdklib.evaluation import ComplianceType, Evaluation, build_annotation

import importlib

import sys
import os

# Get the absolute path of the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path of the project directory
project_dir = os.path.abspath(os.path.join(current_script_dir, "..", ".."))

# Add the project directory to the Python path
sys.path.append(project_dir)

CODE = importlib.import_module("rdklib.evaluation")


class rdklibEvaluationTest(unittest.TestCase):
    def test_build_annotation(self):
        string_0 = ""
        response = CODE.build_annotation(string_0)
        self.assertEqual(response, string_0)

        string_256 = "x" * 256
        response = CODE.build_annotation(string_256)
        self.assertEqual(response, string_256)

        string_257 = string_256 + "x"
        response = CODE.build_annotation(string_257)
        expected_resp = "x" * 244 + " [truncated]"
        self.assertEqual(response, expected_resp)
        self.assertEqual(len(response), 256)

    def test_compliance_type(self):
        # Valid value
        self.assertTrue(CODE.ComplianceType.NOT_APPLICABLE == "NOT_APPLICABLE")
        self.assertTrue(CODE.ComplianceType.COMPLIANT == "COMPLIANT")
        self.assertTrue(CODE.ComplianceType.NON_COMPLIANT == "NON_COMPLIANT")

        # Invalid value
        with self.assertRaises(AttributeError) as context:
            CODE.ComplianceType.SOMETHING_ELSE
        self.assertTrue("SOMETHING_ELSE" in str(context.exception))

    def test_evaluation_init(self):
        # Missing argument Error
        with self.assertRaises(TypeError) as context:
            evaluation = CODE.Evaluation()
        self.assertTrue("__init__()" in str(context.exception))

        # Invalid int argument Error
        with self.assertRaises(Exception) as context:
            evaluation = CODE.Evaluation(4)
        print(str(context.exception))
        self.assertTrue(
            "The complianceType is not valid. Valid values include: ComplianceType.COMPLIANT, ComplianceType.COMPLIANT and ComplianceType.NOT_APPLICABLE"
            in str(context.exception)
        )

        # Invalid str string Error
        with self.assertRaises(Exception) as context:
            evaluation = CODE.Evaluation("string")
        print(str(context.exception))
        self.assertTrue(
            "The complianceType is not valid. Valid values include: ComplianceType.COMPLIANT, ComplianceType.COMPLIANT and ComplianceType.NOT_APPLICABLE"
            in str(context.exception)
        )

        # Default value
        evaluation = CODE.Evaluation(CODE.ComplianceType.COMPLIANT)
        self.assertEqual(evaluation.complianceType, CODE.ComplianceType.COMPLIANT)
        self.assertEqual(evaluation.complianceResourceId, None)
        self.assertEqual(evaluation.complianceResourceType, None)
        self.assertEqual(evaluation.annotation, "")

        # Assigning value
        evaluation = CODE.Evaluation(
            CODE.ComplianceType.COMPLIANT, "some-resource-id", "some-resource-type", "some-annotation"
        )
        self.assertEqual(evaluation.complianceType, CODE.ComplianceType.COMPLIANT)
        self.assertEqual(evaluation.complianceResourceId, "some-resource-id")
        self.assertEqual(evaluation.complianceResourceType, "some-resource-type")
        self.assertEqual(evaluation.annotation, "some-annotation")

    def test_evaluation_eq(self):
        evaluation = CODE.Evaluation(
            CODE.ComplianceType.COMPLIANT, "some-resource-id", "some-resource-type", "some-annotation"
        )
        self.assertTrue(evaluation.__eq__(evaluation))
        self.assertFalse(
            evaluation.__eq__(
                CODE.Evaluation(
                    CODE.ComplianceType.NON_COMPLIANT, "some-resource-id", "some-resource-type", "some-annotation"
                )
            )
        )
        self.assertFalse(
            evaluation.__eq__(
                CODE.Evaluation(
                    CODE.ComplianceType.COMPLIANT, "some-resource-id-2", "some-resource-type", "some-annotation"
                )
            )
        )
        self.assertFalse(
            evaluation.__eq__(
                CODE.Evaluation(
                    CODE.ComplianceType.COMPLIANT, "some-resource-id", "some-resource-type-2", "some-annotation"
                )
            )
        )
        self.assertFalse(
            evaluation.__eq__(CODE.Evaluation(CODE.ComplianceType.COMPLIANT, "some-resource-id", "some-resource-type"))
        )

    def test_import_fields_from_periodic_event(self):
        evaluation = CODE.Evaluation(CODE.ComplianceType.COMPLIANT)
        self.assertEqual(evaluation.orderingTimestamp, None)
        event = {"invokingEvent": json.dumps({"notificationCreationTime": "some-date"})}
        evaluation.import_fields_from_periodic_event(event)
        self.assertEqual(evaluation.orderingTimestamp, "some-date")

    def test_import_fields_from_configuration_item(self):
        config_item = {
            "configurationItemCaptureTime": "some-date",
            "resourceId": "some-resource-id",
            "resourceType": "some-resource-type",
        }
        evaluation = CODE.Evaluation(CODE.ComplianceType.COMPLIANT)
        evaluation.import_fields_from_configuration_item(config_item)
        self.assertEqual(evaluation.complianceResourceId, "some-resource-id")
        self.assertEqual(evaluation.complianceResourceType, "some-resource-type")
        self.assertEqual(evaluation.orderingTimestamp, "some-date")

        evaluation = CODE.Evaluation(CODE.ComplianceType.COMPLIANT, "some-other-id", "some-other-type")
        evaluation.import_fields_from_configuration_item(config_item)
        self.assertEqual(evaluation.complianceResourceId, "some-other-id")
        self.assertEqual(evaluation.complianceResourceType, "some-other-type")

    def test_is_valid(self):
        evaluation = CODE.Evaluation(CODE.ComplianceType.COMPLIANT)
        evaluation.complianceType = None
        with self.assertRaises(Exception) as context:
            evaluation.is_valid()
        self.assertTrue("Missing complianceType from an evaluation result." in str(context.exception))

        evaluation.complianceType = "some-compliance"
        with self.assertRaises(Exception) as context:
            evaluation.is_valid()
        self.assertTrue("Missing complianceResourceId from an evaluation result." in str(context.exception))

        evaluation.complianceResourceId = "some-id"
        with self.assertRaises(Exception) as context:
            evaluation.is_valid()
        self.assertTrue("Missing complianceResourceType from an evaluation result." in str(context.exception))

        evaluation.complianceResourceType = "some-type"
        with self.assertRaises(Exception) as context:
            evaluation.is_valid()
        self.assertTrue("Missing orderingTimestamp from an evaluation result." in str(context.exception))

        evaluation.orderingTimestamp = "some-date"
        self.assertTrue(evaluation.is_valid())

    def test_get_json(self):
        evaluation = CODE.Evaluation(CODE.ComplianceType.NON_COMPLIANT, "some-resource-id", "some-resource-type")
        evaluation.orderingTimestamp = "some-date"
        response = evaluation.get_json()
        resp_expected = {
            "ComplianceResourceId": "some-resource-id",
            "ComplianceResourceType": "some-resource-type",
            "ComplianceType": "NON_COMPLIANT",
            "OrderingTimestamp": "some-date",
        }
        self.assertDictEqual(response, resp_expected)

        evaluation.annotation = "some-annotation"
        response = evaluation.get_json()
        resp_expected = {
            "ComplianceResourceId": "some-resource-id",
            "ComplianceResourceType": "some-resource-type",
            "ComplianceType": "NON_COMPLIANT",
            "OrderingTimestamp": "some-date",
            "Annotation": "some-annotation",
        }
        self.assertDictEqual(response, resp_expected)
