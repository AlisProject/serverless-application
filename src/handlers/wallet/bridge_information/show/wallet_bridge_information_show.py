# -*- coding: utf-8 -*-
import os
import json
from lambda_base import LambdaBase
from decimal_encoder import DecimalEncoder
from private_chain_util import PrivateChainUtil


class WalletBridgeInformationShow(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        max_single_relay_amount = self.__get_max_single_relay_amount()
        min_single_relay_amount = self.__get_min_single_relay_amount()
        relay_fee = self.__get_relay_fee()
        relay_paused = self.__get_relay_paused()

        result = {
            'max_single_relay_amount': max_single_relay_amount,
            'min_single_relay_amount': min_single_relay_amount,
            'relay_fee': relay_fee,
            'relay_paused': relay_paused,
        }

        return {
            'statusCode': 200,
            'body': json.dumps(result, cls=DecimalEncoder)
        }

    @staticmethod
    def __get_max_single_relay_amount():
        return PrivateChainUtil.send_transaction(
            'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/max_single_relay_amount')

    @staticmethod
    def __get_min_single_relay_amount():
        return PrivateChainUtil.send_transaction(
            'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/min_single_relay_amount')

    @staticmethod
    def __get_relay_fee():
        return PrivateChainUtil.send_transaction(
            'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/relay_fee')

    @staticmethod
    def __get_relay_paused():
        return PrivateChainUtil.send_transaction(
            'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/relay_paused')
