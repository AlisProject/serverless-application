import os
import json
from lambda_base import LambdaBase


class MeConfigurationsWalletShow(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        user_configurations = user_configurations_table.get_item(
            Key={'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']})

        return_body = {}
        if user_configurations.get('Item') is not None and \
                user_configurations.get('Item').get('private_eth_address') is not None:
            return_body['wallet_address'] = user_configurations.get('Item')['private_eth_address']
            return_body['salt'] = user_configurations.get('Item')['salt']
            return_body['encrypted_secret_key'] = user_configurations.get('Item')['encrypted_secret_key']

        return {
            'statusCode': 200,
            'body': json.dumps(return_body)
        }
