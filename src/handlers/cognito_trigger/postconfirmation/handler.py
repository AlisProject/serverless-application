# -*- coding: utf-8 -*-
import boto3
from post_confirmation import PostConfirmation

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    postconfirmation = PostConfirmation(event=event, context=context, dynamodb=dynamodb)
    postconfirmation.main()
    return event
