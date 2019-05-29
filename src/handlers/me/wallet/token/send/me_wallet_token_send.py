# -*- coding: utf-8 -*-
import os
import settings
import time
import json
from decimal import Decimal
from db_util import DBUtil
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from private_chain_util import PrivateChainUtil
from time_util import TimeUtil
from jsonschema import validate
from lambda_base import LambdaBase
from jsonschema import ValidationError
from user_util import UserUtil
from exceptions import SendTransactionError, ReceiptError


class MeWalletTokenSend(LambdaBase):

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'recipient_eth_address': settings.parameters['eth_address'],
                'send_value': settings.parameters['token_send_value'],
                'access_token': settings.parameters['access_token'],
                'pin_code': settings.parameters['pin_code']
            },
            'required': ['recipient_eth_address', 'send_value', 'access_token', 'pin_code']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

        # send_value について数値でのチェックを行うため、int に変換
        try:
            self.params['send_value'] = int(self.params['send_value'])
        except ValueError:
            raise ValidationError('send_value must be numeric')

        # pinコードを検証
        self.__validate_pin_code(self.params['access_token'], self.params['pin_code'])

        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        from_user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        recipient_eth_address = self.params['recipient_eth_address']
        send_value = self.params['send_value']
        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        # 日次の限度額を超えていた場合は例外
        sum_price = self.__get_token_send_value_today(user_id)
        if Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) < sum_price + Decimal(send_value):
            raise ValidationError('Token withdrawal limit has been exceeded.')

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

        # token_send_table への書き込み完了後に出金関連の例外が発生した場合は、token_send_table のステータスを fail に更新する
        try:
            # relay 実施
            relay_transaction_hash = self.__relay(from_user_eth_address, recipient_eth_address, send_value,
                                                  transaction_count)
            self.__update_send_info_with_relay_transaction_hash(sort_key, user_id, relay_transaction_hash)
            # transaction の完了を確認
            is_completed = PrivateChainUtil.is_transaction_completed(relay_transaction_hash)
        except SendTransactionError as e:
            # ステータスを fail に更新し中断
            self.__update_send_info_with_send_status(sort_key, user_id, 'fail')
            raise e
        except ReceiptError:
            # send_value の値が残高を超えた場合や、処理最小・最大値の範囲に収まっていない場合に ReceiptError が発生するため
            # ValidationError として処理を中断する
            # ステータスを fail に更新
            self.__update_send_info_with_send_status(sort_key, user_id, 'fail')
            raise ValidationError('send_value')

        # transaction が完了していた場合、ステータスを done に更新
        if is_completed:
            self.__update_send_info_with_send_status(sort_key, user_id, 'done')

        return {
            'statusCode': 200,
            'body': json.dumps({'is_completed': is_completed})
        }

    def __get_token_send_value_today(self, user_id):
        # 今日日付の文字列を取得
        target_date = time.strftime('%Y-%m-%d', time.gmtime(int(time.time())))
        # 今日日付に紐づく出金データを全て取得する
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        query_params = {
            'IndexName': 'target_date-user_id-index',
            'KeyConditionExpression': Key('target_date').eq(target_date) & Key('user_id').eq(user_id)
        }
        result = DBUtil.query_all_items(token_send_table, query_params)
        # 今日日付の出金額の合計を算出（doing の状態も含める）
        # todo: 当 API 処理完了時に send_status が doing となっていたデータについては更新されない状態となっている。
        # 別途 batch 処理等で doing 状態のデータを done or fail に更新させる必要がある。
        return sum([Decimal(i.get('send_value')) for i in result if i.get('send_status') in ['done', 'doing']])

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
        return result

    def __create_send_info_with_approve_transaction_hash(self, sort_key, user_id, approve_transaction_hash):
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        epoch = int(time.time())
        send_info = {
            'user_id': user_id,
            'send_value': self.params['send_value'],
            'approve_transaction': approve_transaction_hash,
            'send_status': 'doing',
            'sort_key': sort_key,
            'created_at': int(time.time()),
            'target_date':  time.strftime('%Y-%m-%d', time.gmtime(epoch))
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

    def __update_send_info_with_send_status(self, sort_key, user_id, send_status):
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        token_send_table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': sort_key
            },
            UpdateExpression='set send_status=:send_status',
            ExpressionAttributeValues={
                ':send_status': send_status,
            }
        )

    def __validate_pin_code(self, access_token, pin_code):
        try:
            self.__verify_user_attribute(access_token, pin_code)
        except ClientError as client_error:
            code = client_error.response['Error']['Code']
            if code == 'NotAuthorizedException':
                raise ValidationError('Access token is invalid')
            elif code == 'CodeMismatchException':
                raise ValidationError('Pin code is invalid')
            elif code == 'ExpiredCodeException':
                raise ValidationError('Pin code is expired')
            elif code == 'LimitExceededException':
                raise ValidationError('Verification limit is exceeded')
            else:
                raise client_error

    def __verify_user_attribute(self, access_token, pin_code):
        self.cognito.verify_user_attribute(
            AccessToken=access_token,
            AttributeName='phone_number',
            Code=pin_code
        )
