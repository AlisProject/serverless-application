# -*- coding: utf-8 -*-
import os
import boto3
import settings
from jsonschema import validate, ValidationError
from lambda_base import LambdaBase


class CustomMessage(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'phone_number': settings.parameters['phone_number']
            }
        }

    def validate_params(self):
        params = self.event['request']['userAttributes']
        if params.get('phone_number', '') != '' and params.get('phone_number_verified', '') != 'true':
            validate(params, self.get_schema())
            client = boto3.client('cognito-idp')
            response = client.list_users(
                    UserPoolId=self.event['userPoolId'],
                    Filter='phone_number = "%s"' % params['phone_number'],
                )
            for user in response['Users']:
                for attribute in user['Attributes']:
                    if attribute['Name'] == 'phone_number_verified' and attribute['Value'] == 'true':
                        raise ValidationError('This phone_number is already exists')

    def exec_main_proc(self):
        if self.event['triggerSource'] == 'CustomMessage_ForgotPassword':
            self.event['response']['smsMessage'] = '{user}さんのパスワード再設定コードは {code} です。'.format(
                user=self.event['userName'], code=self.event['request']['codeParameter'])
            self.event['response']['emailSubject'] = 'パスワード再設定コード'
            self.event['response']['emailMessage'] = "{user}さんのパスワード再設定コードは {code} です".format(
                code=self.event['request']['codeParameter'],
                user=self.event['userName'])
        else:
            self.event['response']['smsMessage'] = '{user}さんの検証コードは {code} です。'.format(
                user=self.event['userName'], code=self.event['request']['codeParameter'])
            self.event['response']['emailSubject'] = 'Email確認リンク'
            self.event['response']['emailMessage'] = "E メールアドレスを検証するには、次のリンクをクリックしてください\n{url}?code={code}&user={user}".format(
                url=os.environ['COGNITO_EMAIL_VERIFY_URL'],
                code=self.event['request']['codeParameter'],
                user=self.event['userName'])
        return self.event
