# -*- coding: utf-8 -*-
import os
import boto3
from lambda_base import LambdaBase


class PostConfirmation(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        users = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = {
            'user_id': self.event["userName"],
            'user_display_name': self.event["userName"]
        }
        users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
        if os.environ['BETA_MODE_FLAG'] == "1":
            beta_users = self.dynamodb.Table(os.environ['BETA_USERS_TABLE_NAME'])
            beta_user = {
                'email': self.event['request']['userAttributes']['email'],
                'used': True
            }
            beta_users.put_item(Item=beta_user)
        return True
