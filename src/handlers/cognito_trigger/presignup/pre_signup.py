# -*- coding: utf-8 -*-
import os
import boto3
import settings
from jsonschema import validate, ValidationError
from lambda_base import LambdaBase
from user_util import UserUtil


class PreSignUp(LambdaBase):
    def get_schema(self):
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

        if params['request']['validationData'] is None or\
                params['request']['validationData'].get('THIRD_PARTY_LOGIN') != 'twitter':
            if UserUtil.check_try_to_register_as_twitter_user(params['userName']):
                raise ValidationError('This username is not allowed')

        validate(params, self.get_schema())
        if params['triggerSource'] == 'PreSignUp_SignUp':
            client = boto3.client('cognito-idp')
            response = client.list_users(
                    UserPoolId=params['userPoolId'],
                    Filter='email = "%s"' % params['request']['userAttributes']['email'],
                )
            for user in response['Users']:
                for attribute in user['Attributes']:
                    if attribute['Name'] == 'email_verified' and attribute['Value'] == 'true':
                        raise ValidationError('This phone_number is already exists')

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
