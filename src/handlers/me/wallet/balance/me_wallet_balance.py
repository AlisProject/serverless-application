# -*- coding: utf-8 -*-
import os
import json
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from lambda_base import LambdaBase


class MeWalletBalance(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']

        return self.__get_balance(address)

    @staticmethod
    def __get_balance(address):
        payload = {dict(private_eth_address=address)}
        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/wallet/balance', auth=auth, payload=payload)
        return json.loads(response.text)
