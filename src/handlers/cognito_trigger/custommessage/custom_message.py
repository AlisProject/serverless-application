# -*- coding: utf-8 -*-
import os
import boto3
import settings
from jsonschema import validate, ValidationError
from cognito_trigger_base import CognitoTriggerBase
from user_util import UserUtil
from private_chain_util import PrivateChainUtil


class CustomMessage(CognitoTriggerBase):
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
           UserUtil.check_try_to_register_as_twitter_user(self.event['userName']) or \
           UserUtil.check_try_to_register_as_yahoo_user(self.event['userName']) or \
           UserUtil.check_try_to_register_as_facebook_user(self.event['userName']):
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
        # セキュリティ観点より、電話番号変更を実行させない。
        # これにより XSS が発生したとしても、電話番号認証が必要な処理は回避が可能
        if self.event['triggerSource'] == 'CustomMessage_VerifyUserAttribute':
            # phone_number_verified が true の場合は電話番号変更を行っていないため当チェックは不要
            if params.get('phone_number_verified', '') != 'true':
                self.__validate_has_not_token(params)

        # サードパーティを利用したユーザの場合、パスワード変更を実行させない
        if self.event['triggerSource'] == 'CustomMessage_ForgotPassword':
            # サードパーティを利用したユーザかを確認
            if UserUtil.is_external_provider_user(self.dynamodb, self.event['userName']):
                raise ValidationError("external provider's user can not execute")

    def exec_main_proc(self):
        if self.event['triggerSource'] == 'CustomMessage_ForgotPassword':
            self.event['response']['smsMessage'] = '{user}さんのパスワード再設定コードは {code} です。'.format(
                user=self.event['userName'], code=self.event['request']['codeParameter'])
            self.event['response']['emailSubject'] = '【ALIS】パスワードの変更：再設定コードの送付'
            self.event['response']['emailMessage'] = "{user}さんのパスワード再設定コードは {code} です".format(
                code=self.event['request']['codeParameter'],
                user=self.event['userName'])
        else:
            self.event['response']['smsMessage'] = 'ALISです。\n{user}さんの認証コードは {code} です。'.format(
                user=self.event['userName'], code=self.event['request']['codeParameter'])
            self.event['response']['emailSubject'] = '【ALIS】登録のご案内：メールアドレスの確認'
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

    # トークンを保持していた場合は例外を出力
    def __validate_has_not_token(self, params):
        address = params.get('custom:private_eth_address')
        if address is None:
            raise ValidationError('Not exists private_eth_address. user_id: ' + self.event['userName'])
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/balance'
        payload = {'private_eth_address': address[2:]}
        token = PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)
        if token is not None and token != '0x0000000000000000000000000000000000000000000000000000000000000000':
            raise ValidationError("Do not allow phone number updates")
