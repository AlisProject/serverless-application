# -*- coding: utf-8 -*-
import os
import json
import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder


class ArticlesPriceShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        # single
        validate(self.params, self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public',
            is_purchased=True
        )

    def exec_main_proc(self):
        params = self.event.get('pathParameters')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': params['article_id']}).get('Item')

        if article_info is None:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Record Not Found'})
            }

        response = {
            'article_id': params['article_id'],
            'price': article_info['price']
        }

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
