import json
import os
import settings

from jsonschema import validate
from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase


class ArticlesEyecatch(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'topic': settings.parameters['topic']
            },
            'required': ['topic']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        screened_article_table = self.dynamodb.Table(os.environ['SCREENED_ARTICLE_TABLE_NAME'])
        eyecatch_articles = screened_article_table.get_item(Key={'article_type': 'eyecatch'}).get('Item')

        if not eyecatch_articles \
                or not eyecatch_articles.get('articles') \
                or not eyecatch_articles.get('articles').get(self.params['topic']):
            items = []
            return {
                'statusCode': 200,
                'body': json.dumps({'Items': items})
            }

        items = [self.__get_public_article(article_id) for article_id in
                 eyecatch_articles.get('articles').get(self.params['topic'])]
        items = [item for item in items if item is not None]

        return {
            'statusCode': 200,
            'body': json.dumps({'Items': items}, cls=DecimalEncoder)
        }

    def __get_public_article(self, article_id):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': article_id}).get('Item')

        if not article_info or not article_info['status'] == 'public':
            return None

        return article_info
