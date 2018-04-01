# -*- coding: utf-8 -*-
import os
import sys
import boto3
import json
import logging
import decimal
import traceback
import settings
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class ArticlesRecent(LambdaBase):
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
        dynamo_tbl = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        limit = int(self.params.get('limit')) if self.params.get('limit') is not None else settings.article_recent_default_limit

        query_params = {
            'Limit': limit,
            'IndexName': 'status-sort_key-index',
            'KeyConditionExpression': Key('status').eq('public'),
            'ScanIndexForward': False
        }

        if self.params.get('article_id') is not None and self.params.get('sort_key') is not None:
            LastEvaluatedKey = {
                'status': 'public',
                'article_id': self.params.get('article_id'),
                'sort_key': self.params.get('sort_key')
            }

            query_params.update({'ExclusiveStartKey': LastEvaluatedKey})

        responce = dynamo_tbl.query(**query_params)

        return {
            'statusCode': 200,
            'body': json.dumps(responce, cls=DecimalEncoder)
        }
