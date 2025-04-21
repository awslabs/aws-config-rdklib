# RDKlib

[![image](https://github.com/awslabs/aws-config-rdklib/workflows/ci/badge.svg?branch=master)](https://github.com/awslabs/aws-config-rdklib/actions?query=workflow%3Aci+branch%3Amaster)

RDKlib is a Python library to enable you to **run custom AWS Config
Rules at scale**. The library can be used to:

- Help you to focus only on the compliance logic, while the library
  does the heavy lifting
- Ease maintenance by moving the boilerplate code as a AWS Lambda
  Layer
- Ease deployment by using AWS Serverless Application Repository

RDKLib works in synergy with the [AWS Config Rule Development Kit](https://github.com/awslabs/aws-config-rdk).

# Getting Started

## Install the library locally

```bash
pip install rdklib
```

## Create a rule using the RDK

The runtime of your RDK rule have to be set to python3.11-lib in the RDK
to provide you the Rule template.

- For periodic trigger:

```bash
    rdk create YOUR_RULE_NAME --runtime python3.11-lib --maximum-frequency TwentyFour_Hours
```

- For configuration change trigger (for example S3 Bucket):

```bash
    rdk create YOUR_RULE_NAME --runtime python3.11-lib --resource-types AWS::S3::Bucket
```

> Note: you need to [install the RDK](https://github.com/awslabs/aws-config-rdk#getting-started) first.

## Deploy your rule with RDKlib layer

RDKLib is designed to work as a AWS Lambda Layer. It allows you to use the library without needing to include it in your deployment package.

1.  Install RDKlib layer (with AWS CLI)

```bash
    aws serverlessrepo create-cloud-formation-change-set --application-id arn:aws:serverlessrepo:ap-southeast-1:711761543063:applications/rdklib --stack-name RDKlib-Layer

    # Copy/paste the full change-set ARN to customize the following command
    aws cloudformation execute-change-set --change-set-name NAME_OF_THE_CHANGE_SET

    aws cloudformation describe-stack-resources --stack-name serverlessrepo-RDKlib-Layer
    # Copy the ARN of the Lambda layer in the "PhysicalResourceId" key (i.e. arn:aws:lambda:YOUR_REGION:YOUR_ACCOUNT:layer:rdklib-layer:1).
```

> Note: You can do the same step manually going to <https://console.aws.amazon.com/lambda/home#/create/function?tab=serverlessApps> and find "rdklib"

1.  Deploy the rule

```bash
    rdk deploy YOUR_RULE_NAME --rdklib-layer-arn YOUR_RDKLIB_LAYER_ARN
```

# FAQs

- Q. What is the `client_factory` that I see in my `rdklib` rules?
    - A. A `client_factory` is a class that allows for dynamic provisioning of a `boto3` client. In an `rdklib` rule, you should treat `client_factory` as the way to create a `boto3` client. So instead of calling `client = boto3.client("s3")`, you would call `client = client_factory.build_client("s3")`.
        - Q. ...Why?
            - A. It's mainly there to allow for unit testing. In a unit testing scenario, your `boto3` client will be replaced with a mock version of the client so that it can perform tests of your rule without making actual calls to AWS.  

# License

This project is licensed under the Apache-2.0 License.

# Feedback / Questions

Feel free to email <rdk-maintainers@amazon.com>

# Contacts

- **Benjamin Morris** - _Maintainer, code, testing_

# Acknowledgements

- **Mark Beacom** - _Maintainer, code, testing_
- **Michael Borchert** - _Design, code, testing, feedback_
- **Ricky Chau** - _Maintainer, code, testing_
- **Julio Delgado Jr.** - *Design, testing, feedback*
- **Chris Gutierrez** - _Design, feedback_
- **Joe Lee** - _Design, feedback_
- **Jonathan Rault** - _Maintainer, design, code, testing, feedback_
- **Carlo DePaolis** - _Maintainer, code, testing_
