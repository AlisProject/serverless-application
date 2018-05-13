# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class ArticlesPopular(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit'],
                'article_id': settings.parameters['article_id'],
                'score': settings.parameters['score'],
                'evaluated_at': settings.parameters['evaluated_at']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())

        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
        article_evaluated_manage = article_evaluated_manage_table.get_item(Key={'type': 'article_score'})

        if article_evaluated_manage.get('Item') is None:
            return {
                'statusCode': 200,
                'body': json.dumps([])
            }

        article_score_table = self.dynamodb.Table(os.environ['ARTICLE_SCORE_TABLE_NAME'])

        limit = settings.articles_popular_default_limit
        if self.params.get('limit'):
            limit = int(self.params.get('limit'))

        query_params = {
            'Limit': limit,
            'IndexName': 'evaluated_at-score-index',
            'KeyConditionExpression': Key('evaluated_at').eq(article_evaluated_manage['Item']['active_evaluated_at']),
            'ScanIndexForward': False
        }

        if self.params.get('article_id') is not None and \
                self.params.get('score') is not None and \
                self.params.get('evaluated_at') is not None:

            LastEvaluatedKey = {
                'evaluated_at': self.params.get('evaluated_at'),
                'article_id': self.params.get('article_id'),
                'score': self.params.get('score')
            }

            query_params.update({'ExclusiveStartKey': LastEvaluatedKey})

        response = article_score_table.query(**query_params)

        articles = []
        for article in response['Items']:
            article_info = article_info_table.get_item(Key={'article_id': article['article_id']}).get('Item')
            if article_info and article_info['status'] == 'public':
                articles.append(article_info)

        results = {'Items': articles}

        if response.get('LastEvaluatedKey'):
            results.update({'LastEvaluatedKey': response['LastEvaluatedKey']})

        return {
            'statusCode': 200,
            'body': json.dumps(results, cls=DecimalEncoder)
        }
