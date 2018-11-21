# -*- coding: utf-8 -*-
import boto3
from pre_authentication import PreAuthentication

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    preauthentication = PreAuthentication(event=event, context=context, dynamodb=dynamodb)
    return preauthentication.main()
