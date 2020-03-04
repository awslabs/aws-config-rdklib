RDKlib
======

RDKlib is a Python library to enable you to **run custom AWS Config Rules at scale**. The library can be used to:

+ Help you to focus only on the compliance logic, while the library does the heavy lifting
+ Ease maintenance by moving the boilerplate code as a AWS Lambda Layer
+ Ease deployment by using AWS Serverless Application Repository

RDKLib works in synergy with the AWS Config Rule Development Kit (https://github.com/awslabs/aws-config-rdk).

Getting Started
===============

Install the library locally
---------------------------

::

    pip install rdklib

Create a rule using the RDK 
---------------------------

The runtime of your RDK rule have to be set to python3.6-lib in the RDK to provide you the Rule template.

* For periodic trigger:

::

    rdk create YOUR_RULE_NAME --runtime python3.6-lib --maximum-frequency TwentyFour_Hours

* For configuration change trigger (for example S3 Bucket)

::

    rdk create YOUR_RULE_NAME --runtime python3.6-lib --resource-types AWS::S3::Bucket

..

    Note: you need to install the RDK (see https://github.com/awslabs/aws-config-rdk#getting-started)

Deploy your rule with RDKlib layer
----------------------------------

RDKLib is designed to work as a AWS Lambda Layer. It allows you to use the library without needing to include it in your deployment package.

1. Install RDKlib layer (with AWS CLI)

::

    aws serverlessrepo create-cloud-formation-change-set --application-id arn:aws:serverlessrepo:ap-southeast-1:711761543063:applications/rdklib --stack-name RDKlib-Layer
    
    # Copy/paste the full change-set ARN to customize the following command
    aws cloudformation execute-change-set --change-set-name NAME_OF_THE_CHANGE_SET

    aws cloudformation describe-stack-resources --stack-name serverlessrepo-RDKlib-Layer
    # Copy the ARN of the Lambda layer in the "PhysicalResourceId" key (i.e. arn:aws:lambda:YOUR_REGION:YOUR_ACCOUNT:layer:rdklib-layer:1).

..

    Note: You can do the same step manually going to `https://console.aws.amazon.com/lambda/home#/create/function?tab=serverlessApps <https://console.aws.amazon.com/lambda/home#/create/function?tab=serverlessApps>`_ and find "rdklib"

2. Deploy the rule

::

    rdk deploy YOUR_RULE_NAME --rdklib-layer-arn YOUR_RDKLIB_LAYER_ARN

Dev Guide
=========

*class* **ClientFactory**
-------------------------

*method* **build_client()**
  Create or reuse a boto3 client. It minimizes the number of STS calls by reusing existing client, if already available.

  **Request Syntax**

  .. code-block:: python

    response = client_factory.build_client(
        service='string')

  **Parameter**

  + **service** *(string)* -- **[REQUIRED]**
  
    The boto3 name of the AWS service
    
*class* **ConfigRule**
----------------------

*method* **evaluate_parameters()**
  Used to analyze the validity of the input parameters of the Config Rule.
  
  **Parameter**
  
  + **rule_parameters** *(dict)*

    The input parameters of the Config Rule.
  
  **Return Syntax**
    If one of the parameters is invalid, raise an InvalidParametersError error.
  
    .. code-block:: python
    
        raise InvalidParametersError("Error message to display")
  
    If the parameters are all valid, return a dict.
  
    .. code-block:: python
    
        return valid_rule_parameters

*method* **evaluate_change()**
  Used to evaluate Configuration Change triggered rule.
  
  **Parameters**
  
  + **event**
  
    Lambda event provided by Config.
  
  + **client_factory** *(ClientFactory)*
  
    *ClientFactory* object to be used in this rule.
  
  + **configuration_item** *(dict)*
  
    The full configuration Item, even if oversized.
  
  + **valid_rule_parameters** *(dict)*
  
    The output of the evaluate_parameters() method.
  
  **Return Syntax**
    Return an list of *Evaluation* object(s). 
  
    .. code-block:: python
    
        return [Evaluation()]
  
    It can be an empty list, if no evaluation.


*method* **evaluate_periodic()**
  Used to evaluate Periodic triggered rule.
  
  **Parameters**
  
  + **event**
  
    Lambda event provided by Config.
  
  + **client_factory** *(ClientFactory)*
  
    *ClientFactory* object to be used in this rule.
  
  + **valid_rule_parameters** *(dict)*
  
    The output of the evaluate_parameters() method.
  
  **Return Syntax**
    Return an list of *Evaluation* object(s). 
  
    .. code-block:: python
    
        return [Evaluation()]
    
    It can be an empty list, if no evaluation.

*class* **Evaluation**
----------------------

Class for the *Evaluation* object.

**Request Syntax**

.. code-block:: python

    evaluation = Evaluation(
        complianceType='ComplianceType',
        complianceResourceId='string',
        annotation='string',
        complianceResourceType='string')

**Parameter**

* **complianceType** *(ComplianceType)* **[REQUIRED]**

  Compliance type of the evaluation.

* **complianceResourceId** *(string)*

  ResourceId of the evaluation. It gets autopopulated for Configuration Change triggered rule.

* **annotation** *(string)*

  Annotation for the evaluation. It gets shorten to 255 characters automatically.

* **complianceResourceType** *(string)*

  ResourceType of the evaluation. It gets autopopulated for Configuration Change triggered rule.

*class* **ComplianceType**
--------------------------

Class for the *ComplianceType* object.

**Request Syntax**

Evaluation will display as "Compliant"

.. code-block:: python

    compliance_type = ComplianceType.COMPLIANT


Evaluation will display as "Non Compliant"

.. code-block:: python

    compliance_type = ComplianceType.NON_COMPLIANT

Evaluation will not display:

.. code-block:: python

    compliance_type = ComplianceType.NOT_APPLICABLE
    
*Helper functions* **rdklibtest**
---------------------------------

*assert_successful_evaluation(\*\*kwargs)*
  Do a comparaison on the list of *Evalation* objects returned by either *evaluate_change()* or *evaluate_periodic()*.
  
  Request Syntax
  
  .. code-block:: python
  
    rdklibtest.assert_successful_evaluation(self, response, resp_expected, evaluations_count=1)
  
  Parameters
    response (list of Evaluation Objects) **[REQUIRED]**
      the list of the response from *evaluate_change()* or *evaluate_periodic()*
    resp_expected (list of Evaluation Objects) **[REQUIRED]**
      the list of the expected response from *evaluate_change()* or *evaluate_periodic()*
    evaluations_count (int)
      The number of Evaluation Objects expected. Default is 1.

  Return
      None

*create_test_configurationchange_event(\*\*kwargs)*
  Generate a dummy configuration change event that can be used as input when testing *evaluate_change()*
  
  Request Syntax
  
  .. code-block:: python
  
    rdklibtest.create_test_configurationchange_event(invoking_event_json, rule_parameters_json=None)

  Parameters
    invoking_event (dict) **[REQUIRED]**
      the invoking event json from Config
    rule_parameters_json (dict)
      the key/value pair(s) for the Rule parameters. Default to None.
  
  Return Syntax

  .. code-block:: python
  
    {
        "configRuleName":"myrule",
        "executionRoleArn":"arn:aws:iam::123456789012:role/example",
        "eventLeftScope": False,
        "invokingEvent": json.dumps(invoking_event_json),
        "accountId": "123456789012",
        "configRuleArn": "arn:aws:config:us-east-1:123456789012:config-rule/config-rule-8fngan",
        "resultToken":"token",
        "ruleParameters": json.dumps(rule_parameters_json)
    }

*create_test_scheduled_event(\*\*kwargs)*
  Generate a dummy periodic event that can be used as input when testing *evaluate_periodic()*

  Request Syntax
  
  .. code-block:: python

    rdklibtest.create_test_scheduled_event(rule_parameters_json=None)

  Parameter
    rule_parameters_json (dict)
      the key/value pair(s) for the Rule parameters. Default to None.

  Return Syntax

  .. code-block:: python
  
    {
        "configRuleName":"myrule",
        "executionRoleArn":"arn:aws:iam::123456789012:role/example",
        "eventLeftScope": False,
        "invokingEvent": "{\"messageType\": \"ScheduledNotification\", \"notificationCreationTime\": \"2017-12-23T22:11:18.158Z\"}",
        "accountId": "123456789012",
        "configRuleArn": "arn:aws:config:us-east-1:123456789012:config-rule/config-rule-8fngan",
        "resultToken":"token",
        "ruleParameters": json.dumps(rule_parameters_json)
    }

License
=======

This project is licensed under the Apache-2.0 License.

Feedback / Questions
====================

Feel free to email rdk-maintainers@amazon.com

Authors
=======
* **Jonathan Rault** - *Maintainer, design, code, testing, feedback*
* **Ricky Chau** - *Maintainer, code, testing*
* **Michael Borchert** - *Design, code, testing, feedback*
* **Joe Lee** - *Design, feedback*
* **Chris Gutierrez** - *Design, feedback*