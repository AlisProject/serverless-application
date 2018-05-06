# -*- coding: utf-8 -*-
import os
import json
import settings
from boto3.dynamodb.conditions import Key, Attr
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class MeArticlesPublicIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit'],
                'article_id': settings.parameters['article_id'],
                'sort_key': settings.parameters['sort_key']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        limit = settings.USERS_ARTICLE_INDEX_DEFAULT_LIMIT
        if self.params.get('limit'):
            limit = int(self.params.get('limit'))

        query_params = {
            'Limit': limit,
            'IndexName': 'user_id-sort_key-index',
            'KeyConditionExpression': Key('user_id').eq(user_id),
            'FilterExpression': Attr('status').eq('public'),
            'ScanIndexForward': False
        }

        if self.params.get('article_id') is not None and self.params.get('sort_key') is not None:
            LastEvaluatedKey = {
                'user_id': user_id,
                'article_id': self.params['article_id'],
                'sort_key': int(self.params['sort_key'])
            }

            query_params.update({'ExclusiveStartKey': LastEvaluatedKey})

        response = article_info_table.query(**query_params)

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
