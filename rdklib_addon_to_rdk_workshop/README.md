# RDKlib Add-On to RDK Workshop

The [RDK Workshop](https://github.com/awslabs/aws-config-rdk/blob/master/rdk-workshop/instructions.md) had the objective to show how a customer can create their own rules (Custom Config Rule) to detect violations on AWS resources and how they can remediate once the rule is violated.

The **RDKlib Add-On** has the objective to take the same example, MFA_ENABLED_RULE created in the **RDK Workshop**, and provide guidance on how to accomplish the solution using the [RDKLib](https://github.com/awslabs/aws-config-rdklib) Python library to enable you to **run custom AWS Config Rules at scale**.  The library can be used to:

- Help you to focus only on the compliance logic, while the library does the heavy lifting
- Ease maintenance by moving the boilerplate code as a AWS Lambda Layer
- Ease deployment by using AWS Serverless Application Repository

## PreRequisites

- Assumes you have knowledge in using [RDK](https://github.com/awslabs/aws-config-rdk), an AWS Config Rules Development Kit that helps developers setup, author, and test custom Config Rules.
- Assumes you have successfully completed the [RDK Workshop](https://github.com/awslabs/aws-config-rdk/blob/master/rdk-workshop/instructions.md)

## Task 1: Install RDKlib locally

    pip install rdklib

## Task 2: Create Rule using RDK with RDKlib

- Periodic Trigger Example:

      rdk create RULE_NAME --runtime python3.11-lib --maximum-frequency TwentyFour_Hours

- Configuration Change Trigger Example (for IAM User)

      rdk create YOUR_RULE_NAME --runtime python3.11-lib --resource-types AWS::IAM::User

## Task 3: Write the Code

- Write Code for MFA_ENABLED_RULEs used in [RDK Workshop](https://github.com/awslabs/aws-config-rdk/blob/master/rdk-workshop/instructions.md) examples to implement the RDKlib.
- For basic solutions to this exercise, scroll to the end.

## Task 4: Install RDKlib layer in AWS

RDKLib is designed to work as a AWS Lambda Layer. It allows you to use the library without needing to include it in your deployment package.

### Install via AWS CLI

1. Create CloudFormation ChangeSet for RDKlib-Layer

       aws serverlessrepo create-cloud-formation-change-set --application-id arn:aws:serverlessrepo:ap-southeast-1:711761543063:applications/rdklib --stack-name RDKlib-Layer

1. Copy/Paste the full change-set ARN to customize the following command and Execute ChangeSet

       aws cloudformation execute-change-set --change-set-name NAME_OF_THE_CHANGE_SET

1. Describe CloudFormation Stack

       aws cloudformation describe-stack-resources --stack-name serverlessrepo-RDKlib-Layer

1. Take Note of the **PhysicalResourceId** as that is the ARN for the **RDKlib Layer**

### Install via AWS Console

1. Create Function from Serverless App Repository.  Click [here](https://console.aws.amazon.com/lambda/home#/create/application?tab=serverlessApps)
1. Search for **rdklib**
1. Deploy
1. Take Note of the **PhysicalResourceId** as that is the ARN for the **RDKlib Layer**
    - CloudFormation -> Stacks -> **serverlessrepo-rdklib** -> Resources

## Task 5: Provide Role to Assume for Lambda Functions

- By default, the Lambda Functions will try to AssumeRole of the AWSServiceConfigRole, which is not allowed.
- You need to provide the Role to Assume for the Lambda Function when its running the code logic you implemented for MFA_ENABLED_RULE.
- This is done by updating the input parameter for **ExecutionRoleName**, and providing the Role Name.

      rdk modify MFA_ENABLED_RULE -i '{"ExecutionRoleName":"ExampleRole"}'

- If using the same Lambda Role that was created by rdk, it will look like this:

      rdk modify MFA_ENABLED_RULE -i '{"ExecutionRoleName":"rdk/MFAENABLEDRULEconfigchangesrdklib-rdkLambdaRole-R0W9ZV90V0HV"}'

## Task 6: Deploy the Rule

    rdk deploy YOUR_RULE_NAME --rdklib-layer-arn YOUR_RDKLIB_LAYER_ARN

## Solutions - MFA_ENABLED_RULE Example with RDKlib

### Triggers on Configuration Change (AWS::IAM::User)

    def evaluate_change(self, event, client_factory, configuration_item, valid_rule_parameters):

        username = configuration_item.get("resourceName")

        iam_client = client_factory.build_client("iam")

        response = iam_client.list_mfa_devices(UserName=username)

        # IAM user has MFA enabled.
        if response["MFADevices"]:
            return [Evaluation(ComplianceType.COMPLIANT)]

        # IAM user has MFA disabled.
        return [Evaluation(ComplianceType.NON_COMPLIANT, annotation="MFA needs to be enabled for user")]

### Triggers Periodic (without Pagination)

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):
        evaluations = []

        iam_client = client_factory.build_client("iam")

        response = iam_client.list_users()

        for user in response["Users"]:
            username = user["UserName"]
            response = iam_client.list_mfa_devices(UserName=username)

            # IAM user has MFA enabled.
            if response["MFADevices"]:
                evaluations.append(Evaluation(ComplianceType.COMPLIANT, username, "AWS::IAM::User"))

            # IAM user has MFA disabled.
            if not response["MFADevices"]:
                annotation = "MFA needs to be enabled for user."
                evaluations.append(
                    Evaluation(ComplianceType.NON_COMPLIANT, username, "AWS::IAM::User", annotation=annotation)
                )
        return evaluations

### Triggers Periodic (with Pagination)

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):

        evaluations = []

        iam_client = client_factory.build_client("iam")

        paginator = iam_client.get_paginator("list_users")
        response_iterator = paginator.paginate()

        for response in response_iterator:
            for user in response["Users"]:
                username = user["UserName"]
                response = iam_client.list_mfa_devices(UserName=username)

                # IAM user has MFA enabled.
                if response["MFADevices"]:
                    evaluations.append(Evaluation(ComplianceType.COMPLIANT, username, "AWS::IAM::User"))
                # IAM user has MFA disabled.
                if not response["MFADevices"]:
                    annotation = "MFA needs to be enabled for user."
                    evaluations.append(
                        Evaluation(ComplianceType.NON_COMPLIANT, username, "AWS::IAM::User", annotation=annotation)
                    )
        return evaluations
