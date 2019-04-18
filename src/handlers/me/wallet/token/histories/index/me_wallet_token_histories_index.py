# -*- coding: utf-8 -*-
import settings
import os
import json
from private_chain_util import PrivateChainUtil
from user_util import UserUtil
from lambda_base import LambdaBase


class MeWalletTokenHistoriesIndex(LambdaBase):

    def get_schema(self):
        pass

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

    def exec_main_proc(self):
        # 履歴取得対象の開始ブロック番号を算出
        to_block = self.__get_current_block_number()
        from_block = str(hex(
            int(to_block, 16) - int(settings.HISTORY_RANGE_DAYS * 24 * 60 * 60 / settings.AVERAGE_BLOCK_TIME)
        ))

        # 開始ブロック番号のタイムスタンプ値を取得
        target_timestamp = self.__get_timestamp_by_block_number(from_block)

        # relay event を取得
        eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        relay_events = self.__get_relay_events_specified_block_range(from_block, to_block, eth_address)

        # apply relay event を取得
        apply_relay_events = self.__get_apply_relay_events_specified_block_range(from_block, to_block, eth_address)

        # 取得した値を返却
        return_params = {
            'timestamp': target_timestamp,
            'relay_events': relay_events,
            'apply_relay_events': apply_relay_events
        }
        return {
            'statusCode': 200,
            'body': json.dumps(return_params)
        }

    def __get_current_block_number(self):
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/block_number'
        return PrivateChainUtil.send_transaction(request_url=url)

    def __get_timestamp_by_block_number(self, block_number):
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/get_block_by_number'
        payload_dict = {
            'block_num': block_number,
        }
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload_dict).get('timestamp')

    def __get_relay_events_specified_block_range(self, from_block, to_block, user_eth_address):
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/relay_events'
        payload_dict = {
            'from_block': from_block,
            'to_block': to_block,
            'sender_eth_address': user_eth_address[2:],
        }
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload_dict)

    def __get_apply_relay_events_specified_block_range(self, from_block, to_block, user_eth_address):
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/apply_relay_events'
        payload_dict = {
            'from_block': from_block,
            'to_block': to_block,
            'recipient_eth_address': user_eth_address[2:],
        }
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload_dict)
