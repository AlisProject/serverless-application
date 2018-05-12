# -*- coding: utf-8 -*-
import boto3
from me_unread_notification_managers_show import MeUnreadNotificationManagersShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_unread_notification_managers_show = MeUnreadNotificationManagersShow(event=event, context=context, dynamodb=dynamodb)
    return me_unread_notification_managers_show.main()
