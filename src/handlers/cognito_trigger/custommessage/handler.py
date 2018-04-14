# -*- coding: utf-8 -*-
import boto3
from custom_message import CustomMessage

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    custommessage = CustomMessage(event=event, context=context, dynamodb=dynamodb)
    return custommessage.main()
