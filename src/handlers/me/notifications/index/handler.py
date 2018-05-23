# -*- coding: utf-8 -*-
import boto3
from me_notifications_index import MeNotificationsIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_notifications_index = MeNotificationsIndex(event=event, context=context, dynamodb=dynamodb)
    return me_notifications_index.main()
