# -*- coding: utf-8 -*-
import boto3
from login_facebook_index import LoginFacebookIndex

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')


def lambda_handler(event, context):
    login_facebook_index = LoginFacebookIndex(
        event=event,
        context=context,
        cognito=cognito,
        dynamodb=dynamodb
    )
    return login_facebook_index.main()
