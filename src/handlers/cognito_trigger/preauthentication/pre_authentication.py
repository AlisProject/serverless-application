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
        sns_user = sns_users_table.get_item(Key={'user_id': params['userName']}).get('Item')
        if sns_user is None:
            try:
                sns_users = sns_users_table.query(
                    IndexName="alias_user_id-index",
                    KeyConditionExpression=Key('alias_user_id').eq(params['userName'])
                )
                if sns_users.get('Count') == 1:
                    sns_user = sns_users.get('Items')[0]
            except ClientError as e:
                logging.fatal(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Internal server error'})
                }

        if (sns_user is not None) and (self.__is_third_party_login_validation_data(params)):
            return self.event
        elif (sns_user is None) and (self.__is_third_party_login_validation_data(params)):
            return self.event
        elif (sns_user is None) and (params['request']['validationData'] == {}):
            return self.event
        else:
            raise ValidationError('Please login with registered sns')

    @staticmethod
    def __is_third_party_login_validation_data(params):
        if (('THIRD_PARTY_LOGIN_MARK' in params['request']['validationData']) and
           (os.environ['THIRD_PARTY_LOGIN_MARK'] == params['request']['validationData']['THIRD_PARTY_LOGIN_MARK'])):
            return True
        return False
