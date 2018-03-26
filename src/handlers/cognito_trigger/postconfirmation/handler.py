# -*- coding: utf-8 -*-
import os
import boto3

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    users = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
    user = {
            'user_id': event["userName"]
            }
    try:
        users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
    except AlreadyExists:
        return event
    return event
