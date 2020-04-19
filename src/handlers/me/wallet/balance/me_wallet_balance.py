import json
from private_chain_util import PrivateChainUtil
from lambda_base import LambdaBase


class MeWalletBalance(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        address = self.event['requestContext']['authorizer']['claims'].get('custom:private_eth_address')
        # 現在のトークン量を取得
        # まだウォレットアドレスを作成していないユーザには 0 を返す
        if address is None:
            balance = '0x0'
        else:
            balance = PrivateChainUtil.get_balance(address)

        return {
            'statusCode': 200,
            'body': json.dumps({'result': balance})
        }
