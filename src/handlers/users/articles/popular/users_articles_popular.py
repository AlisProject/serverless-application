import os
import json
import settings
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class UsersArticlesPopular(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_id': settings.parameters['user_id'],
                'limit': settings.parameters['limit'],
                'article_id': settings.parameters['article_id'],
                'popular_sort_key': settings.parameters['popular_sort_key']
            },
            'required': ['user_id']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        limit = UsersArticlesPopular.get_index_limit(self.params)

        query_params = {
            'Limit': limit,
            'IndexName': 'user_id-popular_sort_key-index',
            'KeyConditionExpression': Key('user_id').eq(self.params['user_id']),
            'FilterExpression': Attr('status').eq('public'),
            'ScanIndexForward': False
        }

        if UsersArticlesPopular.require_last_evaluated_key(self.params):
            last_evaluated_key = {
                'user_id': self.params['user_id'],
                'article_id': self.params['article_id'],
                'popular_sort_key': int(self.params['popular_sort_key'])
            }

            query_params.update({'ExclusiveStartKey': last_evaluated_key})

        response = article_info_table.query(**query_params)

        items = response['Items']

        while 'LastEvaluatedKey' in response and len(response['Items']) < limit:
            query_params.update({'ExclusiveStartKey': response['LastEvaluatedKey']})
            response = article_info_table.query(**query_params)
            items.extend(response['Items'])

            if len(items) >= limit:
                last_evaluated_key = {
                    'user_id': self.params['user_id'],
                    'article_id': items[limit - 1]['article_id'],
                    'popular_sort_key': int(items[limit - 1]['popular_sort_key'])
                }
                response.update({'LastEvaluatedKey': last_evaluated_key})
                break

        response['Items'] = items[:limit]

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }

    @staticmethod
    def get_index_limit(params):
        if params is not None and params.get('limit') is not None:
            return int(params.get('limit'))
        else:
            return settings.USERS_ARTICLE_POPULAR_INDEX_DEFAULT_LIMIT

    @staticmethod
    def require_last_evaluated_key(params):
        if params.get('article_id') is not None and params.get('popular_sort_key') is not None:
            return True
        return False
