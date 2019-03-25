# -*- coding: utf-8 -*-
import json
import os
import settings

from jsonschema import validate
from db_util import DBUtil
from paid_articles_util import PaidArticlesUtil
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
            self.params['article_id']
        )

    def exec_main_proc(self):
        paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])

        paid_article = paid_articles_table.get_item(
            Key={
                'article_id': self.params['article_id'],
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']
            }
        ).get('Item')

        PaidArticlesUtil.validate_paid_article_existence(paid_article)

        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        first_version_article_history = article_history_table.get_item(
            Key={
                'article_id': self.params['article_id'],
                'created_at': paid_article['history_created_at']
            }
        ).get('Item')

        if first_version_article_history is None:
            raise RecordNotFoundError('Record Not Found')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        article_info.update(first_version_article_history)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
