# -*- coding: utf-8 -*-
import os
import boto3
import settings
from jsonschema import validate, ValidationError
from lambda_base import LambdaBase
from user_util import UserUtil


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
        if UserUtil.check_try_to_register_as_line_user(self.event['userName']) or \
           UserUtil.check_try_to_register_as_twitter_user(self.event['userName']):
            raise ValidationError("external provider's user can not execute")
        if params.get('phone_number', '') != '' and \
           params.get('phone_number_verified', '') != 'true' and \
           self.event['triggerSource'] != 'CustomMessage_ForgotPassword':
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
            self.event['response']['smsMessage'] = 'ALISです。\n{user}さんの検証コードは {code} です。'.format(
                user=self.event['userName'], code=self.event['request']['codeParameter'])
            self.event['response']['emailSubject'] = 'Email確認リンク'
            self.event['response']['emailMessage'] = """\
{user}様

ALISをご利用いただきありがとうございます。

仮登録が完了しました。
下記URLにアクセスし、ログインをして登録手続きを完了してください。

https://{domain}/confirm?code={code}&user={user}

※注意事項
・24時間以内に手続きを完了しない場合、上記URLは無効になります。最初から手続きをやり直してください。
・上記URLをクリックしてもページが開かない場合は、URLをコピーし、ブラウザのアドレス欄に貼り付けてください。
・このメールにお心当たりの無い場合は、恐れ入りますが、下記までお問合せください。
 &nbsp;&nbsp; お問合せ（https://{domain}/help）
・このメールアドレスは配信専用となっております。本メールに返信していただきましても、お問合せにはお答えできませんのでご了承ください。

ALIS：https://alismedia.jp
            """.format(
                domain=os.environ['DOMAIN'],
                code=self.event['request']['codeParameter'],
                user=self.event['userName']
            ).replace("\n", "<br />")
        return self.event
