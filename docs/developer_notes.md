# Dev Guide

## _class_ **ClientFactory**

_method_ **build_client()**

Create or reuse a boto3 client. It minimizes the number of STS calls
by reusing existing client, if already available.

**Request Syntax**

```python
response = client_factory.build_client(
    service='string', region='string', assume_role_mode='bool')
```

**Parameters**

- **service** _(string)_ \-- **\[REQUIRED\]**

  The boto3 name of the AWS service

- **region** _(string)_ \-- **\[OPTIONAL\]**

  Default: None The boto3 region

- **assume_role_mode** _(string)_ \-- **\[OPTIONAL\]**

  Default: True By Default, ClientFactory is using AWS Config
  Role, which is comming from Config Rule event.

  1.  User can disable the assume_role_mode by setting it to False
      or set `AssumeRoleMode` to False in Config Rules
      Parameter. ClientFactory will then use the attached lambda
      role for the execution.
  2.  User also can specify a custom role in Config Rules
      Parameter with `ExecutionRoleName` as well as
      `ExecutionRoleRegion` for ClientFactory

## _class_ **ConfigRule**

_method_ **evaluate_parameters()**

Used to analyze the validity of the input parameters of the Config
Rule.

**Parameter**

- **rule_parameters** _(dict)_

  The input parameters of the Config Rule.

**Return Syntax**

If one of the parameters is invalid, raise an
InvalidParametersError error.

```python
from rdklib import InvalidParametersError
raise InvalidParametersError("Error message to display")
```

If the parameters are all valid, return a dict.

```python
return valid_rule_parameters
```

_method_ **evaluate_change()**

Used to evaluate Configuration Change triggered rule.

**Parameters**

- **event**

  Lambda event provided by Config.

- **client_factory** _(ClientFactory)_

  _ClientFactory_ object to be used in this rule.

- **configuration_item** _(dict)_

  The full configuration Item, even if oversized.

- **valid_rule_parameters** _(dict)_

  The output of the evaluate_parameters() method.

**Return Syntax**

Return an list of _Evaluation_ object(s).

```python
return [Evaluation()]
```

It can be an empty list, if no evaluation.

_method_ **evaluate_periodic()**

Used to evaluate Periodic triggered rule.

**Parameters**

- **event**

  Lambda event provided by Config.

- **client_factory** _(ClientFactory)_

  _ClientFactory_ object to be used in this rule.

- **valid_rule_parameters** _(dict)_

  The output of the evaluate_parameters() method.

**Return Syntax**

Return an list of _Evaluation_ object(s).

```python
return [Evaluation()]
```

It can be an empty list, if no evaluation.

## _class_ **Evaluation**

Class for the _Evaluation_ object.

**Request Syntax**

```python
evaluation = Evaluation(
    complianceType='ComplianceType',
    resourceId='string',
    resourceType='string',
    annotation='string')
```

**Parameter**

- **complianceType** _(ComplianceType)_ **\[REQUIRED\]**

  Compliance type of the evaluation.

- **resourceId** _(string)_

  Resource id of the evaluation. It gets autopopulated for
  Configuration Change triggered rule.

- **resourceType** _(string)_

  Resource type of the evaluation (as per AWS CloudFormation
  definition). It gets autopopulated for Configuration Change
  triggered rule.

- **annotation** _(string)_

  Annotation for the evaluation. It gets shorten to 255 characters
  automatically.

## _class_ **ComplianceType**

Class for the _ComplianceType_ object.

**Request Syntax**

Evaluation will display as \"Compliant\"

```python
compliance_type = ComplianceType.COMPLIANT
```

Evaluation will display as \"Non Compliant\"

```python
compliance_type = ComplianceType.NON_COMPLIANT
```

Evaluation will not display:

```python
compliance_type = ComplianceType.NOT_APPLICABLE
```

## _Helper functions_

**rdklibtest**

_assert_successful_evaluation(\*\*kwargs)_

Do a comparison on the list of _Evaluation_ objects returned by
either _evaluate_change()_ or _evaluate_periodic()_.

**Request Syntax**

```python
rdklibtest.assert_successful_evaluation(self, response, resp_expected, evaluations_count=1)
```

**Parameters**

- response (list of Evaluation Objects) **\[REQUIRED\]**

  The list of the response from _evaluate_change()_ or _evaluate_periodic()_

- resp_expected (list of Evaluation Objects) **\[REQUIRED\]**

  The list of the expected response from _evaluate_change()_ or _evaluate_periodic()_

- evaluations_count (int)

  The number of Evaluation Objects expected. Default is 1.

**Return**

    None

**_create_test_configurationchange_event(\*\*kwargs)_**

Generate a dummy configuration change event that can be used as
input when testing `_evaluate_change()_`

**Request Syntax**

```python
rdklibtest.create_test_configurationchange_event(invoking_event_json, rule_parameters_json=None)
```

Parameters

- invoking_event (dict) **\[REQUIRED\]**

  the invoking event json from Config

- rule_parameters_json (dict)

  the key/value pair(s) for the Rule parameters. Default to None.

**Return Syntax**

```python
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
```

**_create_test_scheduled_event(\*\*kwargs)_**

Generate a dummy periodic event that can be used as input when
testing `_evaluate_periodic()_`

**Request Syntax**

```python
rdklibtest.create_test_scheduled_event(rule_parameters_json=None)
```

**Parameter**

- rule_parameters_json (dict)

  the key/value pair(s) for the Rule parameters. Default to None.

**Return Syntax**

```python
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
```
