# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from db_util import DBUtil


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
            is_purchased=True
        )
        DBUtil.validate_user_existence(
            self.dynamodb,
            self.event['requestContext']['authorizer']['claims']['cognito:username']
        )

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        article_content['body'] = article_content['paid_body']
        article_content.pop('paid_body', None)

        article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
