import json
from private_chain_util import PrivateChainUtil
from lambda_base import LambdaBase


class MeWalletAllowanceShow(LambdaBase):

    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        from_user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']

        # allowance を取得
        allowance = PrivateChainUtil.get_allowance(from_user_eth_address)

        return {
            'statusCode': 200,
            'body': json.dumps({'allowance': allowance})
        }
