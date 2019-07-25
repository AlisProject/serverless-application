# -*- coding: utf-8 -*-
import os
import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from exceptions import LimitExceeded


class MeConfiguresMuteUsersAdd(LambdaBase):
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
        # 自分自身でないことを確認
        if self.params['mute_user_id'] == self.event['requestContext']['authorizer']['claims']['cognito:username']:
            raise ValidationError(self.params['mute_user_id'] + ' is own user.')

    def exec_main_proc(self):
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])

        # 登録数制限の確認
        user_configurations = user_configurations_table.get_item(Key={
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']
        })
        if user_configurations.get('Item') is not None and \
                user_configurations.get('Item').get('mute_users') is not None and \
                len(user_configurations.get('Item').get('mute_users')) >= settings.MUTE_USERS_MAX_COUNT:
            raise LimitExceeded('mute users')

        # ミュートユーザ追加（mute_users 項目として set で管理する）
        user_configurations_table.update_item(
            Key={
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            },
            UpdateExpression="add mute_users :mute_users",
            ExpressionAttributeValues={':mute_users': {self.params['mute_user_id']}}
        )

        return {
            'statusCode': 200
        }
