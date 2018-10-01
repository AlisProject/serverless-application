# -*- coding: utf-8 -*-
import os
from lambda_base import LambdaBase
from jsonschema import ValidationError


class PreAuthentication(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        params = self.event
        sns_users_table = self.dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
        sns_user = sns_users_table.get_item(Key={'user_id': params['userName']}).get('Item')

        if (sns_user is not None) and (os.environ['LINE_LOGIN_MARK'] == params['request']['validationData']['THIRD_PARTY_LOGIN']):
            return self.event
        elif (os.environ['LINE_LOGIN_MARK'] == params['request']['validationData']['THIRD_PARTY_LOGIN']) and ('first' == params['request']['validationData']['FIRST_LOGIN']):
            return self.event
        elif (sns_user is None) and (params['request']['validationData'] is None):
            return self.event
        else:
            raise ValidationError('Please login with registered sns')
