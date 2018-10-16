import boto3
from login_line_authorize_request import LoginLineAuthorizeRequest

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    login_line_authorize_request = LoginLineAuthorizeRequest(event=event, context=context, dynamodb=dynamodb, cognito=cognito)
    return login_line_authorize_request.main()
