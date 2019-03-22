# -*- coding: utf-8 -*-
import json
import os
import settings

from jsonschema import validate
from db_util import DBUtil
from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from not_authorized_error import NotAuthorizedError
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
                'article_id': self.params['article_id'],
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']
            }
        )

        paid_article_item = paid_article.get('Item')
        if paid_article_item is None or paid_article_item['status'] != 'done':
            raise NotAuthorizedError('Forbidden')

        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        first_version_article_history = article_history_table.get_item(
            Key={
                'article_id': self.params['article_id'],
                'created_at': paid_article_item['history_created_at']
            }
        )
        first_version_article_history_item = first_version_article_history.get('Item')
        if first_version_article_history_item is None:
            raise RecordNotFoundError('Record Not Found')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        if article_info is None or article_content is None:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Record Not Found'})
            }

        article_content['body'] = first_version_article_history_item['body']
        article_content['title'] = first_version_article_history_item['title']
        article_content['created_at'] = first_version_article_history_item['created_at']
        article_content.pop('paid_body', None)

        article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
