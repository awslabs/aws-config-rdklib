import json
import boto3
import os

from rdklib import Evaluator, Evaluation, ConfigRule, ComplianceType, ClientFactory
from rdklib.evaluation import build_annotation

RESOURCE_TYPE = 'AWS::::Account'

class CognitoUserPoolRule (ConfigRule):
        
    # for handling the periodic config notifications, implement evaluate_periodic method  
    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):

        evaluations = []
        client_factory = ClientFactory(self.get_execution_role_arn(event))
        
        pool_list={}
        response=[]
    
        try:
            cognitoclient = client_factory.build_client('cognito-idp')
        except:
            annotation = build_annotation('Unable to get Cognito client access')
            evaluations.append(Evaluation(
                        ComplianceType.NON_COMPLIANT, {},
                        resourceType=RESOURCE_TYPE,
                        annotation=annotation))
            return evaluations
    
        next_batch = cognitoclient.list_user_pools(MaxResults=50)
    
        # check if there are more results
        if 'NetToken' in next_batch:
            response += next_batch
            while 'NetToken' in next_batch:
                next_batch = cognitoclient.list_user_pools(
                                                        MaxResults=50,
                                                        NextToken=next_batch['NextToken']
                                                    )
                response += next_batch
    
        response = next_batch['UserPools']
    
        poolids = [poolidlist['Id'] for poolidlist in response]
        
        for a in response:
            pool_list[a['Id']] = a['Name']
    
        for poolid in poolids:
            response = cognitoclient.list_identity_providers(UserPoolId=poolid)
    
            # for local user database, there won't be any identity providers
            if not response['Providers']:
                annotation = build_annotation('No SAML or OIDC providers for user pool {}:{}'.format(poolid, pool_list[poolid]))
                evaluations.append(Evaluation(
                            ComplianceType.NON_COMPLIANT, pool_list[poolid],
                            resourceType=RESOURCE_TYPE,
                            annotation=annotation))
                return evaluations

            else:
                for providers in response['Providers']:
                    id_response = cognitoclient.describe_identity_provider(
                                                    UserPoolId=poolid,
                                                    ProviderName=providers['ProviderName']
                                                )['IdentityProvider']
    
                    if not ((id_response['ProviderType'] == 'SAML') or (id_response['ProviderType'] == 'OIDC')):
                        annotation = build_annotation('User pool {} with identity provider {} of type {}'.format(id_response['UserPoolId'], id_response['ProviderName'], id_response['ProviderType']))
                        evaluations.append(Evaluation(
                                    ComplianceType.NON_COMPLIANT, pool_list[poolid],
                                    resourceType=RESOURCE_TYPE,
                                    annotation=annotation))
                        return evaluations

    
        annotation = build_annotation('Compliant')
        evaluations.append(Evaluation(
                        ComplianceType.COMPLIANT, {},
                        resourceType=RESOURCE_TYPE,
                        annotation=annotation))
        return evaluations

def lambda_handler(event, context):

    # create an instance of the Config rule which is set to periodically evaluate Cognito user pool
    cognitouserpool_rule = CognitoUserPoolRule()
    
    # Execution role for Config rule evaluation can either be set as Config rule parameter or can be set through
    # Lambda environment variable. Since this Config rule to evaluate Cognito user pool is evaluated in security 
    # account, setting an execution role configured in security account
     
    role = os.environ['RULE_EXECUTION_ROLE']
    cognitouserpool_rule.set_execution_arn(role)
    
    evaluator = Evaluator(cognitouserpool_rule)
    return evaluator.handle(event, context)

