# -*- coding: utf-8 -*-
import boto3
from post_confirmation import PostConfirmation

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    postconfirmation = PostConfirmation(event=event, context=context, dynamodb=dynamodb, cognito=cognito)
    postconfirmation.main()
    return event
