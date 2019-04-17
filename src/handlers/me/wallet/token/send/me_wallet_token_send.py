# -*- coding: utf-8 -*-
import os
import settings
import time
from private_chain_util import PrivateChainUtil
from time_util import TimeUtil
from jsonschema import validate
from lambda_base import LambdaBase
from jsonschema import ValidationError
from user_util import UserUtil


class MeWalletTokenSend(LambdaBase):

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'recipient_eth_address': settings.parameters['eth_address'],
                'send_value': settings.parameters['token_send_value'],
            },
            'required': ['recipient_eth_address', 'send_value']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

        # send_value について数値でのチェックを行うため、int に変換
        try:
            self.params['send_value'] = int(self.params['send_value'])
        except ValueError:
            raise ValidationError('send_value must be numeric')
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        from_user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        recipient_eth_address = self.params['recipient_eth_address']
        send_value = self.params['send_value']
        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        # allowance を取得
        allowance = self.__get_allowance(from_user_eth_address)
        # transaction_count を取得
        transaction_count = self.__get_transaction_count(from_user_eth_address)
        # 既に approve されている場合（allowance の戻り値が "0x0" ではない場合）、該当の approve を削除する（0 で更新）
        if allowance != '0x0':
            self.__approve(from_user_eth_address, 0, transaction_count)
            transaction_count = self.__increment_transaction_count(transaction_count)

        # approve 実施
        approve_transaction_hash = self.__approve(from_user_eth_address, send_value, transaction_count)
        transaction_count = self.__increment_transaction_count(transaction_count)
        self.__create_send_info_with_approve_transaction_hash(sort_key, user_id, approve_transaction_hash)

        # relay 実施
        relay_transaction_hash = self.__relay(from_user_eth_address, recipient_eth_address, send_value,
                                              transaction_count)
        self.__update_send_info_with_relay_transaction_hash(sort_key, user_id, relay_transaction_hash)

        return {
            'statusCode': 200
        }

    @staticmethod
    def __get_allowance(from_user_eth_address):
        payload = {
            'from_user_eth_address': from_user_eth_address,
            'owner_eth_address': from_user_eth_address[2:],
            'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        }
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/allowance'
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)

    @staticmethod
    def __get_transaction_count(from_user_eth_address):
        payload = {
            'from_user_eth_address': from_user_eth_address
        }
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/get_transaction_count'
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)

    @staticmethod
    def __increment_transaction_count(hex_str):
        return str(hex(int(hex_str, 16) + 1))

    @staticmethod
    def __approve(from_user_eth_address, send_value, nonce):
        payload = {
            'from_user_eth_address': from_user_eth_address,
            'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:],
            'nonce': nonce,
            'value': format(send_value, '064x')
        }
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/approve'
        # approve 実施
        result = PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)
        return result

    @staticmethod
    def __relay(from_user_eth_address, recipient_eth_address, send_value, nonce):
        payload = {
            'from_user_eth_address': from_user_eth_address,
            'recipient_eth_address': recipient_eth_address[2:],
            'nonce': nonce,
            'amount': format(send_value, '064x')
        }
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/relay'
        # relay 実施
        result = PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)
        # transaction の完了を確認
        PrivateChainUtil.validate_transaction_completed(result)
        return result

    def __create_send_info_with_approve_transaction_hash(self, sort_key, user_id, approve_transaction_hash):
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        send_info = {
            'user_id': user_id,
            'send_value': self.params['send_value'],
            'approve_transaction': approve_transaction_hash,
            'uncompleted': 1,
            'sort_key': sort_key,
            'created_at': int(time.time())
        }

        token_send_table.put_item(
            Item=send_info,
            ConditionExpression='attribute_not_exists(user_id)'
        )

    def __update_send_info_with_relay_transaction_hash(self, sort_key, user_id, relay_transaction_hash):
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        token_send_table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': sort_key
            },
            UpdateExpression='set relay_transaction_hash=:relay_transaction_hash',
            ExpressionAttributeValues={
                ':relay_transaction_hash': relay_transaction_hash,
            }
        )
