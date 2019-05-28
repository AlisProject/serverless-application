# -*- coding: utf-8 -*-
import logging
import os
import traceback
from decimal import Decimal

import settings
import json
import requests
import time

from private_chain_util import PrivateChainUtil
from time_util import TimeUtil
from db_util import DBUtil
from aws_requests_auth.aws_auth import AWSRequestsAuth
from jsonschema import validate
from lambda_base import LambdaBase
from jsonschema import ValidationError
from record_not_found_error import RecordNotFoundError
from exceptions import SendTransactionError
from user_util import UserUtil


class MeWalletTip(LambdaBase):

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'tip_value': settings.parameters['tip_value'],
            },
            'required': ['article_id', 'tip_value']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        # single
        # tip_value について数値でのチェックを行うため、int に変換
        try:
            self.params['tip_value'] = int(self.params['tip_value'])
        except ValueError:
            raise ValidationError('Tip value must be numeric')
        validate(self.params, self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public'
        )

    def exec_main_proc(self):
        # get article info
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        # validation
        # does not tip same user
        if article_info['user_id'] == self.event['requestContext']['authorizer']['claims']['cognito:username']:
            raise ValidationError('Can not tip to myself')

        # send tip
        headers = {'content-type': 'application/json'}
        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')

        from_user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        to_user_eth_address = self.__get_user_private_eth_address(article_info['user_id'])
        tip_value = self.params['tip_value']
        transaction_hash = self.__send_tip(from_user_eth_address, to_user_eth_address, tip_value, auth, headers)

        burn_transaction = None
        try:
            # 投げ銭が成功した時のみバーン処理を行う
            if PrivateChainUtil.is_transaction_completed(transaction_hash):
                # バーンのトランザクション処理
                burn_transaction = self.__burn_transaction(tip_value, from_user_eth_address, auth, headers)
        except Exception as err:
            logging.fatal(err)
            traceback.print_exc()
        finally:
            # create tip info
            self.__create_tip_info(transaction_hash, burn_transaction, article_info)

        return {
            'statusCode': 200
        }

    @staticmethod
    def __send_tip(from_user_eth_address, to_user_eth_address, tip_value, auth, headers):
        payload = json.dumps(
            {
                'from_user_eth_address': from_user_eth_address,
                'to_user_eth_address': to_user_eth_address[2:],
                'tip_value': format(tip_value, '064x')
            }
        )
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/wallet/tip', auth=auth, headers=headers, data=payload)

        # exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))

        # return transaction hash
        return json.dumps(json.loads(response.text).get('result')).replace('"', '')

    def __create_tip_info(self, transaction_hash, burn_transaction, article_info):
        tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])

        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        epoch = int(time.time())

        tip_info = {
            'user_id': user_id,
            'to_user_id': article_info['user_id'],
            'tip_value': self.params['tip_value'],
            'article_id': self.params['article_id'],
            'article_title': article_info['title'],
            'transaction': transaction_hash,
            'burn_transaction': burn_transaction,
            'uncompleted': 1,
            'sort_key': sort_key,
            'target_date': time.strftime('%Y-%m-%d', time.gmtime(epoch)),
            'created_at': epoch
        }

        tip_table.put_item(
            Item=tip_info,
            ConditionExpression='attribute_not_exists(user_id)'
        )

    def __get_user_private_eth_address(self, user_id):
        # user_id に紐づく private_eth_address を取得
        user_info = UserUtil.get_cognito_user_info(self.cognito, user_id)
        private_eth_address = [a for a in user_info['UserAttributes'] if a.get('Name') == 'custom:private_eth_address']
        # private_eth_address が存在しないケースは想定していないため、取得出来ない場合は例外とする
        if len(private_eth_address) != 1:
            raise RecordNotFoundError('Record Not Found: private_eth_address')

        return private_eth_address[0]['Value']

    @staticmethod
    def __burn_transaction(price, user_eth_address, auth, headers):
        burn_token = format(int(Decimal(price) / Decimal(10)), '064x')

        burn_payload = json.dumps(
            {
                'from_user_eth_address': user_eth_address,
                'to_user_eth_address': settings.ETH_ZERO_ADDRESS,
                'tip_value': burn_token
            }
        )

        # burn transaction
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/wallet/tip', auth=auth, headers=headers, data=burn_payload)

        # validate status code
        if response.status_code != 200:
            raise SendTransactionError('status code not 200')

        # exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))

        return json.loads(response.text).get('result').replace('"', '')
