# -*- coding: utf-8 -*-
import os
import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate


class MeConfigurationsMuteUsersDelete(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'mute_user_id': settings.parameters['user_id']
            },
            'required': ['mute_user_id']
        }

    def validate_params(self):
        # single
        validate(self.params, self.get_schema())
        # relation
        DBUtil.validate_user_existence(
            self.dynamodb,
            self.params['mute_user_id']
        )

    def exec_main_proc(self):
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])

        # ミュートユーザ追加
        user_configurations_table.update_item(
            Key={
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            },
            UpdateExpression="delete mute_users :mute_users",
            ExpressionAttributeValues={':mute_users': {self.params['mute_user_id']}}
        )

        return {
            'statusCode': 200
        }
