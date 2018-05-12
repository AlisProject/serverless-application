# -*- coding: utf-8 -*-
import boto3
from me_unread_notification_managers_update import MeUnreadNotificationManagersUpdate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_unread_notification_managers_update = MeUnreadNotificationManagersUpdate(event=event, context=context, dynamodb=dynamodb)
    return me_unread_notification_managers_update.main()
