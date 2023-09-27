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

class ComplianceType:
    NOT_APPLICABLE = "NOT_APPLICABLE"
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"

    @staticmethod
    def get_valid_compliances():
        return [ComplianceType.NOT_APPLICABLE, ComplianceType.COMPLIANT, ComplianceType.NON_COMPLIANT]

class Evaluation:
    annotation = ""
    complianceResourceType = None
    complianceType = None
    complianceResourceId = None
    orderingTimestamp = None

    def __init__(self, complianceType, resourceId=None, resourceType=None, annotation=""):
        self.annotation = build_annotation(annotation)
        self.complianceResourceId = resourceId
        self.complianceResourceType = resourceType
        if not complianceType in ComplianceType.get_valid_compliances():
            print('The complianceType is not valid. Valid values include: ComplianceType.COMPLIANT, ComplianceType.COMPLIANT and ComplianceType.NOT_APPLICABLE')
            raise Exception('The complianceType is not valid. Valid values include: ComplianceType.COMPLIANT, ComplianceType.COMPLIANT and ComplianceType.NOT_APPLICABLE')
        self.complianceType = complianceType

    def __repr__(self):
        return f"Evaluation(annotation='{self.annotation}', complianceResourceId='{self.complianceResourceId}', complianceResourceType='{self.complianceResourceType}', complianceType='{self.complianceType}')"

    def __eq__(self, other):
        return (
            (
                (self.annotation is None and other.annotation is None) or
                (self.annotation == other.annotation)
            ) and
            self.complianceResourceType == other.complianceResourceType and
            self.complianceType == other.complianceType and
            self.complianceResourceId == other.complianceResourceId and
            self.orderingTimestamp == other.orderingTimestamp)

    # This generate an evaluation for config
    def import_fields_from_periodic_event(self, event):
        self.orderingTimestamp = str(json.loads(event['invokingEvent'])['notificationCreationTime'])

    def import_fields_from_configuration_item(self, configuration_item):
        self.orderingTimestamp = configuration_item['configurationItemCaptureTime']
        if not self.complianceResourceId:
            self.complianceResourceId = configuration_item['resourceId']
        if not self.complianceResourceType:
            self.complianceResourceType = configuration_item['resourceType']

    # Check that an evaluation is well-formed
    def is_valid(self):
        if not self.complianceType:
            print('Missing complianceType from an evaluation result.')
            raise Exception('Missing complianceType from an evaluation result.')

        if not self.complianceResourceId:
            print('Missing complianceResourceId from an evaluation result.')
            raise Exception('Missing complianceResourceId from an evaluation result.')

        if not self.complianceResourceType:
            print('Missing complianceResourceType from an evaluation result.')
            raise Exception('Missing complianceResourceType from an evaluation result.')

        if not self.orderingTimestamp:
            print('Missing orderingTimestamp from an evaluation result.')
            raise Exception('Missing orderingTimestamp from an evaluation result.')

        return True

    def get_json(self):
        output = {
            "ComplianceResourceId": self.complianceResourceId,
            "ComplianceResourceType": self.complianceResourceType,
            "ComplianceType": self.complianceType,
            "OrderingTimestamp": self.orderingTimestamp
        }

        if self.annotation:
            output["Annotation"] = self.annotation

        return output

# Build annotation within Service constraints
def build_annotation(annotation_string):
    if len(annotation_string) > 256:
        return annotation_string[:244] + " [truncated]"
    return annotation_string
