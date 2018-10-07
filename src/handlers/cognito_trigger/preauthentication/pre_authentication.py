# -*- coding: utf-8 -*-
import os
import json
import logging
from lambda_base import LambdaBase
from jsonschema import ValidationError
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


class PreAuthentication(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        params = self.event
        sns_users_table = self.dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
        # alias_user_idを追加する前
        sns_user = sns_users_table.get_item(Key={'user_id': params['userName']}).get('Item')
        # alias_user_idを追加した後のsns_userの判断
        if sns_user is None:
            try:
                sns_user = sns_users_table.query(
                    IndexName="alias_user_id-index",
                    KeyConditionExpression=Key('alias_user_id').eq(params['userName'])
                )
                if sns_user.get('Count') == 1:
                    sns_user = sns_user.get('Items')[0]
            except ClientError as e:
                logging.fatal(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Internal server error'})
                }

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
