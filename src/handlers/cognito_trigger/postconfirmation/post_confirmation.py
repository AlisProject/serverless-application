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
                'user_id': self.event["userName"]
                }
        users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
        return True
