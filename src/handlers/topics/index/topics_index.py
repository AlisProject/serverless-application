# -*- coding: utf-8 -*-
import json
import os

import settings
from boto3.dynamodb.conditions import Key
from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase


class TopicsIndex(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        topic_table = self.dynamodb.Table(os.environ['TOPIC_TABLE_NAME'])

        query_params = {
            'IndexName': 'index_hash_key-order-index',
            'KeyConditionExpression': Key('index_hash_key').eq(settings.TOPIC_INDEX_HASH_KEY)
        }

        topics = topic_table.query(**query_params)['Items']

        return {
            'statusCode': 200,
            'body': json.dumps(topics, cls=DecimalEncoder)
        }
