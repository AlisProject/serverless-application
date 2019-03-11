# -*- coding: utf-8 -*-
import boto3
from login_facebook_authorization_url import LoginFacebookAuthorizationUrl

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    login_facebook_authorization_url = LoginFacebookAuthorizationUrl(
        dynamodb=dynamodb,
        event=event,
        context=context
    )
    return login_facebook_authorization_url.main()
