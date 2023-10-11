def process_evaluations(event, client_factory, evaluations):
    config_client = client_factory.build_client('config')

    print(f'DEBUG: processing evaluations = {evaluations}')

    # Put together the request that reports the evaluation status
    result_token = event['resultToken']
    test_mode = False
    if result_token == 'TESTMODE':
        print('DEBUG: result token was test mode')
        # Used solely for RDK test to skip actual put_evaluation API call
        test_mode = True

    if not evaluations:
        print('DEBUG: no evaluations found')
        config_client.put_evaluations(Evaluations=[], ResultToken=result_token, TestMode=test_mode)
        return []


    # Invoke the Config API to report the result of the evaluation
    evaluation_copy = []
    evaluation_copy = evaluations[:]
    while evaluation_copy:
        print('DEBUG: in evaluation while loop')
        config_client.put_evaluations(Evaluations=evaluation_copy[:100], ResultToken=result_token, TestMode=test_mode)
        del evaluation_copy[:100]

    # Used solely for RDK test to be able to test Lambda function
    return evaluations
