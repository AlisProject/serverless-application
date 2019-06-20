# -*- coding: utf-8 -*-
import os
import settings
from jsonschema import validate, ValidationError
from lambda_base import LambdaBase
from not_authorized_error import NotAuthorizedError
from user_util import UserUtil


# Todo: LambdaBase → CognitoTriggerBase への変更
class PreSignUp(LambdaBase):
    def get_schema(self):
        params = self.event
        # TwitterのIDは30文字以下なので条件分岐を作成していない
        if params.get('triggerSource') == 'PreSignUp_AdminCreateUser' and \
           UserUtil.check_try_to_register_as_line_user(params['userName']):
            return {
                'type': 'object',
                'properties': {
                    'userName': settings.parameters['line_id']
                }
            }
        elif params.get('triggerSource') == 'PreSignUp_AdminCreateUser' and \
            UserUtil.check_try_to_register_as_yahoo_user(
                params['userName']):
            return {
                'type': 'object',
                'properties': {
                    'userName': settings.parameters['yahoo_id']
                }
            }
        elif params.get('triggerSource') == 'PreSignUp_AdminCreateUser' and \
            UserUtil.check_try_to_register_as_facebook_user(
                params['userName']):
            return {
                'type': 'object',
                'properties': {
                    'userName': settings.parameters['facebook_id']
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

            # 通常サインアップユーザーにTwitter・LINE・Yahoo・Facebookから始まる名前を許可しないバリデーション
            if params['request']['validationData'] is None or \
                   params['request']['validationData'].get('EXTERNAL_PROVIDER_LOGIN_MARK') != \
                   os.environ['EXTERNAL_PROVIDER_LOGIN_MARK']:
                if UserUtil.check_try_to_register_as_twitter_user(params['userName']):
                    raise ValidationError('This username is not allowed')
                if UserUtil.check_try_to_register_as_line_user(params['userName']):
                    raise ValidationError('This username is not allowed')
                if UserUtil.check_try_to_register_as_yahoo_user(params['userName']):
                    raise ValidationError('This username is not allowed')
                if UserUtil.check_try_to_register_as_facebook_user(params['userName']):
                    raise ValidationError('This username is not allowed')

            response = self.__filter_users(self.cognito, params)
            self.__email_exist_check(response)
        elif params['triggerSource'] == 'PreSignUp_AdminCreateUser':
            if (params['request'].get('validationData') is not None) and \
                   params['request']['validationData'].get('EXTERNAL_PROVIDER_LOGIN_MARK') == \
                   os.environ['EXTERNAL_PROVIDER_LOGIN_MARK']:
                response = self.__filter_users(self.cognito, params)
                self.__email_exist_check(response)
            else:
                raise NotAuthorizedError('Forbidden')
        # 現状CognitoTriggerは'PreSignUp_SignUp','PreSignUp_AdminCreateUser'の２種類のみなので異なるTriggerがリクエストされた場合は例外にする
        else:
            raise Exception

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

    @staticmethod
    def __filter_users(cognito, params):
        return cognito.list_users(
            UserPoolId=params['userPoolId'],
            Filter='email = "%s"' % params['request']['userAttributes']['email'],
        )
