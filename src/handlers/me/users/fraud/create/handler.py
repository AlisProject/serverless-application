import boto3
from me_users_fraud_create import MeUsersFraudCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_users_fraud_create = MeUsersFraudCreate(event=event, context=context, dynamodb=dynamodb)
    return me_users_fraud_create.main()
