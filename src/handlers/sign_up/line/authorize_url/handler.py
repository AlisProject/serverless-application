import boto3
from sign_up_line_authorize_url import SignUpLineAuthorizeUrl

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    sign_up_line_authorize_url = SignUpLineAuthorizeUrl(event=event, context=context, dynamodb=dynamodb, cognito=cognito)
    return sign_up_line_authorize_url.main()
