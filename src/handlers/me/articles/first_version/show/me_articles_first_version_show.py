# -*- coding: utf-8 -*-
import json
import os
import settings

from jsonschema import validate
from db_util import DBUtil
from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from record_not_found_error import RecordNotFoundError


class MeArticlesFirstVersionShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            is_purchased=True
        )

    def exec_main_proc(self):
        paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])

        paid_article = paid_articles_table.get_item(
            Key={
                'article_id': self.event['pathParameters']['article_id'],
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']
            }
        )
        if paid_article.get('Item') is None:
            raise RecordNotFoundError('Record Not Found')

        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        first_version_article_history = article_history_table.get_item(
            Key={
                'article_id': self.event['pathParameters']['article_id'],
                'created_at': paid_article.get('Item')['history_created_at']
            }
        )
        if first_version_article_history.get('Item') is None:
            raise RecordNotFoundError('Record Not Found')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        params = self.event.get('pathParameters')
        article_info = article_info_table.get_item(Key={'article_id': params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': params['article_id']}).get('Item')

        if article_info is None or article_content is None:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Record Not Found'})
            }

        article_content['body'] = article_content['paid_body']
        article_content.pop('paid_body', None)

        article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
