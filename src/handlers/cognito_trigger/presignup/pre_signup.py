# -*- coding: utf-8 -*-
import os
import settings
import re
from jsonschema import validate, ValidationError
from lambda_base import LambdaBase


class PreSignUp(LambdaBase):
    def get_schema(self):
        params = self.event
        if 'triggerSource' in params and params['triggerSource'] == 'PreSignUp_AdminCreateUser' and re.match('^LINE_U', params['userName']):
            return {
                'type': 'object',
                'properties': {
                    'userName': settings.parameters['line_id']
                }
            }
        else:
            return {
                'type': 'object',
                'properties': {
                    'userName': settings.parameters['user_id']
                }
            }

    def validate_params(self):
        params = self.event
        if params['userName'] in settings.ng_user_name:
            raise ValidationError('This username is not allowed')
        validate(params, self.get_schema())
        if params['triggerSource'] == 'PreSignUp_SignUp':
            response = self.cognito.list_users(
                    UserPoolId=params['userPoolId'],
                    Filter='email = "%s"' % params['request']['userAttributes']['email'],
                )
            self.__email_exist_check(response)
        elif params['triggerSource'] == 'PreSignUp_AdminCreateUser':
            response = self.cognito.list_users(
                UserPoolId=params['userPoolId'],
                Filter='email = "%s"' % params['request']['userAttributes']['email'],
            )
            self.__email_exist_check(response)

    def exec_main_proc(self):
        if os.environ['BETA_MODE_FLAG'] == "1":
            beta_table = self.dynamodb.Table(os.environ['BETA_USERS_TABLE_NAME'])
            item = beta_table.get_item(
                Key={
                    'email': self.event['request']['userAttributes']['email']
                }
            )
            if item.get('Item', False) and item['Item']['used'] is False:
                return self.event
            else:
                raise "This email address is not avalilable"
        else:
            return self.event

    @staticmethod
    def __email_exist_check(response):
        for user in response['Users']:
            for attribute in user['Attributes']:
                if attribute['Name'] == 'email_verified' and attribute['Value'] == 'true':
                    raise ValidationError('This email is already exists')
