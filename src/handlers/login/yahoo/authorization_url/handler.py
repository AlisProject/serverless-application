# -*- coding: utf-8 -*-
import boto3
from login_yahoo_authorization_url import LoginYahooAuthorizationUrl

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    login_yahoo_authorization_url = LoginYahooAuthorizationUrl(
        dynamodb=dynamodb,
        event=event,
        context=context
    )
    return login_yahoo_authorization_url.main()
