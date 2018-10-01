import boto3
from login_line import LoginLine

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    login_line = LoginLine(event=event, context=context, dynamodb=dynamodb, cognito=cognito)
    return login_line.main()
