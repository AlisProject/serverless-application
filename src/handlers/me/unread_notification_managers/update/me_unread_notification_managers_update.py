# -*- coding: utf-8 -*-
import os
from lambda_base import LambdaBase


class MeUnreadNotificationManagersUpdate(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        unread_notification_manager_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': False}
        )

        return {
            'statusCode': 200
        }
