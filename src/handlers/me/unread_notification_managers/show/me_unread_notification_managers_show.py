# -*- coding: utf-8 -*-
import os
import json
from lambda_base import LambdaBase


class MeUnreadNotificationManagersShow(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        manager = unread_notification_manager_table.get_item(Key={'user_id': user_id}).get('Item')

        unread = True if manager and manager['unread'] else False

        return {
            'statusCode': 200,
            'body': json.dumps({'unread': unread})
        }
