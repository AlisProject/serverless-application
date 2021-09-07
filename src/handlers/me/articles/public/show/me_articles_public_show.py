# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder
from db_util import DBUtil


class MeArticlesPublicShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')

        validate(self.event.get('pathParameters'), self.get_schema())

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='public'
        )

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        aricle_private_info_table = self.dynamodb.Table(os.environ['ARTICLE_PRIVATE_INFO_TABLE_NAME'])

        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        aricle_private_info = aricle_private_info_table.get_item(Key={'article_id': self.params['article_id']}).get(
            'Item')

        # add paid_body
        if 'price' in article_info:
            article_content['body'] = article_content['paid_body']
            article_content.pop('paid_body', None)
        article_info.update(article_content)

        # add pv_counts
        if aricle_private_info is None or aricle_private_info.get('pv_counts') is None:
            article_info['pv_counts'] = 0
        else:
            article_info['pv_counts'] = aricle_private_info['pv_counts']

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
