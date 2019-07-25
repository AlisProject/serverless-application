# -*- coding: utf-8 -*-
import os
import json
from lambda_base import LambdaBase


class MeConfiguresMuteUsersIndex(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        user_configurations = user_configurations_table.get_item(
            Key={'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']})

        mute_users = []
        if user_configurations.get('Item') is not None and \
                user_configurations.get('Item').get('mute_users') is not None:
            # mute_users は set形 のため list形 へ変更
            mute_users = list(user_configurations.get('Item').get('mute_users'))
            # user_id の昇順でソート
            mute_users.sort()

        return_body = {
            'mute_users': mute_users
        }

        return {
            'statusCode': 200,
            'body': json.dumps(return_body)
        }
