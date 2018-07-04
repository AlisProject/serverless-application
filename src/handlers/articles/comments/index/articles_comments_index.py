# -*- coding: utf-8 -*-
import os
import json
import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class ArticlesCommentsIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit'],
                'article_id': settings.parameters['article_id'],
                'comment_id': settings.parameters['comment']['comment_id'],
                'sort_key': settings.parameters['sort_key']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

        DBUtil.validate_article_existence(self.dynamodb, self.params['article_id'], status='public')

    def exec_main_proc(self):
        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])

        limit = settings.COMMENT_INDEX_DEFAULT_LIMIT
        if self.params.get('limit'):
            limit = int(self.params.get('limit'))

        query_params = {
            'Limit': limit,
            'IndexName': 'article_id-sort_key-index',
            'KeyConditionExpression': Key('article_id').eq(self.params.get('article_id')),
            'ScanIndexForward': False
        }

        if self.params.get('comment_id') is not None and self.params.get('sort_key') is not None:
            last_evaluated_key = {
                'comment_id': self.params['comment_id'],
                'article_id': self.params['article_id'],
                'sort_key': int(self.params['sort_key'])
            }

            query_params.update({'ExclusiveStartKey': last_evaluated_key})

        response = comment_table.query(**query_params)

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
