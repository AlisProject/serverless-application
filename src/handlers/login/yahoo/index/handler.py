# -*- coding: utf-8 -*-
import boto3
from login_yahoo_index import LoginYahooIndex

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')


def lambda_handler(event, context):
    login_yahoo_index = LoginYahooIndex(
        event=event,
        context=context,
        cognito=cognito,
        dynamodb=dynamodb
    )
    return login_yahoo_index.main()
