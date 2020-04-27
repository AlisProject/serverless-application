import json
from private_chain_util import PrivateChainUtil
from lambda_base import LambdaBase
from user_util import UserUtil


class MeWalletBalance(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        address = self.event['requestContext']['authorizer']['claims'].get('custom:private_eth_address')

        # 現在のトークン量を取得
        # まだウォレットアドレスを作成していないユーザには 0 を返す
        if address is None:
            balance = '0x0'
        elif not UserUtil.exists_private_eth_address(self.dynamodb, user_id):
            # Cognito上にprivate_eth_addressは存在するが、カストディ規制のウォレット移行が完了していないユーザにも0を返す
            balance = '0x0'
        else:
            balance = PrivateChainUtil.get_balance(address)

        return {
            'statusCode': 200,
            'body': json.dumps({'result': balance})
        }
