# -*- coding: utf-8 -*-
import boto3
from login_twitter_index import LoginTwitterIndex

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')


def lambda_handler(event, context):
    login_twitter_index = LoginTwitterIndex(
        event=event,
        context=context,
        dynamodb=dynamodb,
        cognito=cognito
    )
    return login_twitter_index.main()
