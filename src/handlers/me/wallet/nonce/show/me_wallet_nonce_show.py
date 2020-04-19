import json
from lambda_base import LambdaBase
from private_chain_util import PrivateChainUtil


class MeWalletNonceShow(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        address = self.event['requestContext']['authorizer']['claims'].get('custom:private_eth_address')

        # nonce を取得
        if address is None:
            # まだウォレットアドレスを作成していないユーザには 0 を返す
            nonce = '0x0'
        else:
            nonce = PrivateChainUtil.get_transaction_count(address)

        return {
            'statusCode': 200,
            'body': json.dumps({'nonce': nonce})
        }
