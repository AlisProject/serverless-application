# -*- coding: utf-8 -*-
import logging
import os
import traceback
from decimal import Decimal

import settings
import time

from private_chain_util import PrivateChainUtil
from time_util import TimeUtil
from db_util import DBUtil
from jsonschema import validate
from lambda_base import LambdaBase
from jsonschema import ValidationError
from user_util import UserUtil


class MeWalletTip(LambdaBase):

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'tip_signed_transaction': settings.parameters['raw_transaction'],
                'burn_signed_transaction': settings.parameters['raw_transaction']
            },
            'required': ['article_id', 'tip_signed_transaction', 'burn_signed_transaction']
        }

    def validate_params(self):
        # 認証・ウォレット情報が登録済であること
        UserUtil.verified_phone_and_email(self.event)
        UserUtil.validate_private_eth_address(self.dynamodb,
                                              self.event['requestContext']['authorizer']['claims']['cognito:username'])

        # single
        validate(self.params, self.get_schema())
        # 署名が正しいこと
        PrivateChainUtil.validate_raw_transaction_signature(
            self.params['tip_signed_transaction'],
            self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        )
        PrivateChainUtil.validate_raw_transaction_signature(
            self.params['burn_signed_transaction'],
            self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        )

        # relation
        # 公開されている記事であること
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public'
        )

    def exec_main_proc(self):
        ################
        # get parameter
        ################
        # article info
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        # eth_address
        from_user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        to_user_eth_address = UserUtil.get_private_eth_address(self.cognito, article_info['user_id'])
        # transaction_count
        transaction_count = PrivateChainUtil.get_transaction_count(from_user_eth_address)

        ################
        # validation
        ################
        # does not tip same user
        if article_info['user_id'] == self.event['requestContext']['authorizer']['claims']['cognito:username']:
            raise ValidationError('Can not tip to myself')

        # validate raw_transaction
        # tip
        tip_data = PrivateChainUtil.get_data_from_raw_transaction(
            self.params['tip_signed_transaction'],
            transaction_count
        )
        PrivateChainUtil.validate_erc20_transfer_data(tip_data, to_user_eth_address)
        # burn
        transaction_count = PrivateChainUtil.increment_transaction_count(transaction_count)
        burn_data = PrivateChainUtil.get_data_from_raw_transaction(
            self.params['burn_signed_transaction'],
            transaction_count
        )
        PrivateChainUtil.validate_erc20_transfer_data(burn_data, '0x' + os.environ['BURN_ADDRESS'])

        # burn 量が正しいこと
        tip_value = int(tip_data[72:], 16)
        burn_value = int(burn_data[72:], 16)
        calc_burn_value = int(Decimal(tip_value) / Decimal(10))
        if burn_value != calc_burn_value:
            raise ValidationError('burn_value is invalid.')

        # 残高が足りていること
        if not self.__is_burnable_user(from_user_eth_address, tip_value, burn_value):
            raise ValidationError('Required at least {token} token'.format(token=tip_value + burn_value))

        #######################
        # send_raw_transaction
        #######################
        transaction_hash = PrivateChainUtil.send_raw_transaction(self.params['tip_signed_transaction'])
        burn_transaction = None
        try:
            # 投げ銭が成功した時のみバーン処理を行う
            if PrivateChainUtil.is_transaction_completed(transaction_hash):
                # バーンのトランザクション処理
                burn_transaction = PrivateChainUtil.send_raw_transaction(self.params['burn_signed_transaction'])
            else:
                logging.info('Burn was not executed because tip transaction was uncompleted.')
        except Exception as err:
            logging.fatal(err)
            traceback.print_exc()
        finally:
            # create tip info
            self.__create_tip_info(transaction_hash, tip_value, burn_transaction, article_info)

        return {
            'statusCode': 200
        }

    @staticmethod
    def __is_burnable_user(eth_address, tip_value, burn_value):
        # get_balance
        token = PrivateChainUtil.get_balance(eth_address)

        # return result
        if int(token, 16) >= tip_value + burn_value:
            return True
        return False

    def __create_tip_info(self, transaction_hash, tip_value, burn_transaction, article_info):
        tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])

        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        epoch = int(time.time())

        tip_info = {
            'user_id': user_id,
            'to_user_id': article_info['user_id'],
            'tip_value': tip_value,
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
