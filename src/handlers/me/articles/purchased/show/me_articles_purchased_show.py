# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from db_util import DBUtil
from not_authorized_error import NotAuthorizedError


class MeArticlesPurchasedShow(LambdaBase):
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
            status='public',
        )

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])

        paid_article = paid_articles_table.get_item(
            Key={
                'article_id': self.params['article_id'],
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']
            }
        ).get('Item')

        if paid_article is None or paid_article['status'] != 'done':
            raise NotAuthorizedError('Forbidden')

        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        # 記事が有料から無料になるケースを考慮し、有料記事の場合のみ body の書き換えを行う
        if 'price' in article_info:
            article_content['body'] = article_content['paid_body']
            article_content.pop('paid_body', None)

        article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
