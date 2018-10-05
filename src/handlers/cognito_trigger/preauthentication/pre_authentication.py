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

        if (sns_user is not None) and (params['request']['validationData'] is not None) and \
           (self.__is_third_party_login_validation_data(params)):
            return self.event
        elif (params['request']['validationData'] is not None) and \
             (self.__is_third_party_login_validation_data(params)) and \
             (self.__is_first_login(params)):
            return self.event
        elif (sns_user is None) and (params['request']['validationData'] is None):
            return self.event
        else:
            raise ValidationError('Please login with registered sns')

    @staticmethod
    def __is_third_party_login_validation_data(params):
        if (os.environ['LINE_LOGIN_MARK'] == params['request']['validationData']['THIRD_PARTY_LOGIN']) or \
           ('twitter' == params['request']['validationData']['THIRD_PARTY_LOGIN']):
            return True
        return False

    @staticmethod
    def __is_first_login(params):
        if ('FIRST_LOGIN' in params['request']['validationData']) and \
           ('first' == params['request']['validationData']['FIRST_LOGIN']):
            return True
        return False
