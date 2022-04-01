import json
import botocore

# Helper function used to validate input
def check_defined(reference, reference_name):
    if not reference:
        raise Exception('Error: ' + reference_name + ' is not defined.')
    return reference

# Check whether the resource has been deleted. If it has, then the evaluation is unnecessary.
def is_applicable_status(configuration_item, event, **kwargs):
    status = configuration_item['configurationItemStatus']
    is_applicable = kwargs.get('is_applicable', None)
    event_left_scope = event['eventLeftScope']
    if is_applicable:
        return True
    if status in ('ResourceDeleted', 'ResourceDeletedNotRecorded', 'ResourceNotRecorded'):
        print("Resource Deleted, setting Compliance Status to NOT_APPLICABLE.")
    return status in ('OK', 'ResourceDiscovered') and not event_left_scope

# Check whether the resource type for the CI is in scope for the rule - if not, we can skip evaluation
def is_applicable_resource_type(configuration_item, expected_resource_types):
    if configuration_item['resourceType'] not in expected_resource_types:
        print("ResourceType is not in expected resource types")
    return configuration_item['resourceType'] in expected_resource_types

# Based on the type of message get the configuration item
# either from configurationItem in the invoking event
# or using the getResourceConfigHistiry API in getConfiguration function.
def get_configuration_item(invoking_event):
    check_defined(invoking_event, 'invokingEvent')
    return check_defined(invoking_event['configurationItem'], 'configurationItem')

def is_internal_error(exception):
    return (
        not isinstance(exception, botocore.exceptions.ClientError) or
        exception.response['Error']['Code'].startswith('5') or
        'InternalError' in exception.response['Error']['Code'] or
        'ServiceError' in exception.response['Error']['Code']
        )

def build_internal_error_response(internal_error_message, internal_error_details=None):
    return build_error_response(internal_error_message, internal_error_details)

def build_error_response(internal_error_message, internal_error_details=None, customer_error_code=None, customer_error_message=None):
    error_response = {
        'internalErrorMessage': internal_error_message,
        'internalErrorDetails': internal_error_details,
        'customerErrorMessage': customer_error_message,
        'customerErrorCode': customer_error_code
    }
    print(error_response)
    return error_response

# Build an error to be displayed in the logs when the parameter is invalid.
def build_parameters_value_error_response(ex):
    """Return an error dictionary when the evaluate_parameters() raises a ValueError.

    Keyword arguments:
    ex -- Exception text
    """
    return  build_error_response(internal_error_message="Parameter value is invalid",
                                 internal_error_details="A ValueError was raised during the validation of the Parameter value",
                                 customer_error_code="InvalidParameterValueException",
                                 customer_error_message=str(ex))

# Check whether the message is OversizedConfigurationItemChangeNotification or not
def is_oversized_changed_notification(message_type):
    check_defined(message_type, 'messageType')
    return message_type == 'OversizedConfigurationItemChangeNotification'

# Check whether the message is a ScheduledNotification or not.
def is_scheduled_notification(message_type):
    check_defined(message_type, 'messageType')
    return message_type == 'ScheduledNotification'

def inflate_oversized_notification(config_client, invoking_event):
    grh_response = get_resource_config_history(config_client, invoking_event)
    config_item = convert_into_notification_config_item(grh_response['configurationItems'][0])
    return {
        'configurationItem': config_item,
        'notificationCreationTime': invoking_event['notificationCreationTime'],
        'messageType': invoking_event['messageType'],
        'recordVersion': invoking_event['recordVersion']
    }

def get_resource_config_history(config_client, invoking_event):
    resource_id = invoking_event['configurationItemSummary']['resourceId']
    resource_type = invoking_event['configurationItemSummary']['resourceType']
    return config_client.get_resource_config_history(
        resourceType=resource_type,
        resourceId=resource_id,
        limit=1
    )

def convert_into_notification_config_item(grh_config_item):
    return {
        'configurationItemCaptureTime': grh_config_item['configurationItemCaptureTime'],
        'configurationStateId': grh_config_item['configurationStateId'],
        'awsAccountId': grh_config_item['accountId'],
        'configurationItemStatus': grh_config_item['configurationItemStatus'],
        'resourceType': grh_config_item['resourceType'],
        'resourceId': grh_config_item['resourceId'],
        'resourceName': grh_config_item['resourceName'],
        'ARN': grh_config_item['arn'],
        'awsRegion': grh_config_item['awsRegion'],
        'availabilityZone': grh_config_item['availabilityZone'],
        'configurationStateMd5Hash': grh_config_item['configurationItemMD5Hash'],
        'resourceCreationTime': grh_config_item['resourceCreationTime'],
        'relatedEvents': grh_config_item['relatedEvents'],
        'tags': grh_config_item['tags'],
        'relationships': extract_relationships(grh_config_item['relationships']),
        'configuration': json.loads(grh_config_item['configuration']),
        'supplementaryConfiguration': extract_supplementary_configuration(grh_config_item['supplementaryConfiguration'])
    }

def extract_supplementary_configuration(grh_supplementary_configuration):
    return {key: json.loads(value) for key, value in
            grh_supplementary_configuration.items()}

def extract_relationships(grh_relationships):
    return [{'name': relationship['relationshipName'],
             'resourceId': relationship['resourceId'],
             'resourceName': relationship['resourceName'],
             'resourceType': relationship['resourceType']} for relationship in grh_relationships]
