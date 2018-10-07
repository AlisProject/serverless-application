# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class UsersArticlesPublic(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_id': settings.parameters['user_id'],
                'limit': settings.parameters['limit'],
                'article_id': settings.parameters['article_id'],
                'sort_key': settings.parameters['sort_key']
            },
            'required': ['user_id']
        }

    def validate_params(self):
        params = self.event.get('pathParameters')

        if params is None:
            raise ValidationError('pathParameters is required')

        if self.event.get('queryStringParameters') is not None:
            params.update(self.event.get('queryStringParameters'))
        ParameterUtil.cast_parameter_to_int(params, self.get_schema())

        validate(params, self.get_schema())

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        limit = self.__get_index_limit(self.event.get('queryStringParameters'))

        query_params = {
            'Limit': limit,
            'IndexName': 'user_id-sort_key-index',
            'KeyConditionExpression': Key('user_id').eq(self.event['pathParameters']['user_id']),
            'FilterExpression': Attr('status').eq('public'),
            'ScanIndexForward': False
        }

        if self.__require_last_evaluatd_key(self.event.get('queryStringParameters')):
            LastEvaluatedKey = {
                'user_id': self.event['pathParameters']['user_id'],
                'article_id': self.event['queryStringParameters']['article_id'],
                'sort_key': int(self.event['queryStringParameters']['sort_key'])
            }

            query_params.update({'ExclusiveStartKey': LastEvaluatedKey})

        response = article_info_table.query(**query_params)

        items = response['Items']

        while 'LastEvaluatedKey' in response and len(response['Items']) < limit:
            query_params.update({'ExclusiveStartKey': response['LastEvaluatedKey']})
            response = article_info_table.query(**query_params)
            items.extend(response['Items'])

            if len(items) >= limit:
                LastEvaluatedKey = {
                    'user_id': self.params['user_id'],
                    'article_id': items[limit - 1]['article_id'],
                    'sort_key': int(items[limit - 1]['sort_key'])
                }
                response.update({'LastEvaluatedKey': LastEvaluatedKey})
                break

        response['Items'] = items[:limit]

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }

    def __get_index_limit(self, params):
        if params is not None and params.get('limit') is not None:
            return int(params.get('limit'))
        else:
            return settings.USERS_ARTICLE_INDEX_DEFAULT_LIMIT

    def __require_last_evaluatd_key(self, params):
        if params is None:
            return False

        return params.get('article_id') is not None and params.get('sort_key') is not None
