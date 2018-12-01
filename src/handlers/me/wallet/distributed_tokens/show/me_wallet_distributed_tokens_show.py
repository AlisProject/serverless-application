import json
import os

from boto3.dynamodb.conditions import Key

from db_util import DBUtil
from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase


class MeWalletDistributedTokensShow(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        token_distribution_table = self.dynamodb.Table(os.environ['TOKEN_DISTRIBUTION_TABLE_NAME'])

        query_params = {
            'IndexName': 'user_id-sort_key-index',
            'KeyConditionExpression': Key('user_id').eq(user_id)
        }
        items = DBUtil.query_all_items(token_distribution_table, query_params)

        result = {
            'article': 0,
            'like': 0,
            'tip': 0,
            'bonus': 0
        }
        for item in items:
            result[item['distribution_type']] += item['quantity']

        return {
            'statusCode': 200,
            'body': json.dumps(result, cls=DecimalEncoder)
        }
