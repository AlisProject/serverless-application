# -*- coding: utf-8 -*-
import os
import settings
from private_chain_util import PrivateChainUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from user_util import UserUtil


class MeConfigurationsWalletAdd(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'wallet_address': settings.parameters['eth_address'],
                'salt': settings.parameters['wallet_salt'],
                'encrypted_secret_key': settings.parameters['encrypted_secret_key'],
                'signature': settings.parameters['eth_signature_schema']
            },
            'required': ['wallet_address', 'salt', 'encrypted_secret_key', 'signature']
        }

    def validate_params(self):
        # single
        validate(self.params, self.get_schema())
        # relational
        PrivateChainUtil.validate_message_signature(
            self.event['requestContext']['authorizer']['claims']['cognito:username'],
            self.params['signature'],
            self.params['wallet_address']
        )
        # 既に登録済みの場合は処理中断
        if UserUtil.exists_private_eth_address(self.dynamodb,
                                               self.event['requestContext']['authorizer']['claims']['cognito:username']):
            raise ValidationError('private_eth_address is exists.')

    def exec_main_proc(self):
        # ウォレット情報の登録パラメータ作成
        update_expression = "set private_eth_address = :private_eth_address" \
                            ", salt = :salt" \
                            ", encrypted_secret_key = :encrypted_secret_key"
        expression_attribute_values = {
            ':private_eth_address': self.params['wallet_address'],
            ':salt': self.params['salt'],
            ':encrypted_secret_key': self.params['encrypted_secret_key']
        }
        # 旧アドレスが存在する場合はパラメータに追加
        old_eth_address = self.event['requestContext']['authorizer']['claims'].get('custom:private_eth_address')
        if old_eth_address is not None:
            update_expression += ', old_private_eth_address = :old_private_eth_address'
            expression_attribute_values[':old_private_eth_address'] = old_eth_address

        # ウォレット情報をDBに登録
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        user_configurations_table.update_item(
            Key={
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        # ウォレットアドレスを cognito に登録
        self.update_private_eth_address(self.params['wallet_address'])

        return {
            'statusCode': 200
        }

    def update_private_eth_address(self, private_eth_address):
        self.cognito.admin_update_user_attributes(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            UserAttributes=[
                {
                    'Name': 'custom:private_eth_address',
                    'Value': private_eth_address
                },
            ]
        )
