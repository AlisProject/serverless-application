import json
import settings
from user_util import UserUtil
from lambda_base import LambdaBase
from jsonschema import validate


class UsersWalletAddressShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_id': settings.parameters['user_id']
            },
            'required': ['user_id']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        # get private_eth_address
        private_eth_address = UserUtil.get_private_eth_address(self.cognito, self.params['user_id'])

        return {
            'statusCode': 200,
            'body': json.dumps({'wallet_address': private_eth_address})
        }
