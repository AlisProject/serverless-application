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
                'init_approve_signed_transaction': settings.parameters['raw_transaction'],
                'approve_signed_transaction': settings.parameters['raw_transaction'],
                'relay_signed_transaction': settings.parameters['raw_transaction'],
                'access_token': settings.parameters['access_token'],
                'pin_code': settings.parameters['pin_code']
            },
            'required': ['approve_signed_transaction', 'relay_signed_transaction', 'pin_code']
        }

    def validate_params(self):
        # 認証・ウォレット情報が登録済であること
        UserUtil.verified_phone_and_email(self.event)
        UserUtil.validate_private_eth_address(self.dynamodb,
                                              self.event['requestContext']['authorizer']['claims']['cognito:username'])
        # single
        validate(self.params, self.get_schema())
        # 署名が正しいこと
        if self.params.get('init_approve_signed_transaction') is not None:
            PrivateChainUtil.validate_raw_transaction_signature(
                self.params['init_approve_signed_transaction'],
                self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
            )
        PrivateChainUtil.validate_raw_transaction_signature(
            self.params['approve_signed_transaction'],
            self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        )
        PrivateChainUtil.validate_raw_transaction_signature(
            self.params['relay_signed_transaction'],
            self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        )

        # pinコードを検証
        self.__validate_pin_code(self.params['access_token'], self.params['pin_code'])

    def exec_main_proc(self):
        ################
        # get parameter
        ################
        sort_key = TimeUtil.generate_sort_key()
        from_user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        allowance = PrivateChainUtil.get_allowance(from_user_eth_address)
        transaction_count = PrivateChainUtil.get_transaction_count(from_user_eth_address)

        ################
        # validation
        ################
        # validate raw_transaction
        # init_approve_signed_transaction
        if allowance != '0x0':
            # allowance が設定されている場合は必須
            if self.params.get('init_approve_signed_transaction') is None:
                raise ValidationError('init_approve_signed_transaction is invalid.')
            # data
            init_approve_data = PrivateChainUtil.get_data_from_raw_transaction(
                self.params['init_approve_signed_transaction'],
                transaction_count
            )
            PrivateChainUtil.validate_erc20_approve_data(init_approve_data)
            if int(init_approve_data[72:], 16) != 0:
                raise ValidationError('Value of init_approve is invalid.')
            transaction_count = PrivateChainUtil.increment_transaction_count(transaction_count)

        # approve_signed_transaction
        approve_data = PrivateChainUtil.get_data_from_raw_transaction(
            self.params['approve_signed_transaction'],
            transaction_count
        )
        PrivateChainUtil.validate_erc20_approve_data(approve_data)
        # 日次の限度額を超えていた場合は例外
        sum_price = self.__get_token_send_value_today(user_id)
        if Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) < sum_price + Decimal(int(approve_data[72:], 16)):
            raise ValidationError('Token withdrawal limit has been exceeded.')
        transaction_count = PrivateChainUtil.increment_transaction_count(transaction_count)

        # relay_signed_transaction
        relay_data = PrivateChainUtil.get_data_from_raw_transaction(
            self.params['relay_signed_transaction'],
            transaction_count
        )
        PrivateChainUtil.validate_erc20_relay_data(relay_data)
        # approve と relay の value が同一であること
        approve_value = int(approve_data[72:], 16)
        relay_value = int(relay_data[72:], 16)
        if approve_value != relay_value:
            raise ValidationError('approve and relay values do not match.')

        #######################
        # send_raw_transaction
        #######################
        # 既に approve されている場合（allowance の戻り値が "0x0" ではない場合）、該当の approve を削除する（0 で更新）
        if allowance != '0x0':
            PrivateChainUtil.send_raw_transaction(self.params.get('init_approve_signed_transaction'))

        # approve 実施
        approve_transaction_hash = PrivateChainUtil.send_raw_transaction(self.params.get('approve_signed_transaction'))
        self.__create_send_info_with_approve_transaction_hash(
            sort_key, user_id, approve_transaction_hash, relay_value
        )

        # token_send_table への書き込み完了後に出金関連の例外が発生した場合は、token_send_table のステータスを fail に更新する
        try:
            # relay 実施
            relay_transaction_hash = PrivateChainUtil.send_raw_transaction(self.params.get('relay_signed_transaction'))
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

    def __create_send_info_with_approve_transaction_hash(self, sort_key, user_id, approve_transaction_hash, send_value):
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        epoch = int(time.time())
        send_info = {
            'user_id': user_id,
            'send_value': send_value,
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
