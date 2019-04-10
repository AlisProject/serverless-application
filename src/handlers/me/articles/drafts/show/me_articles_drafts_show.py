# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder
from db_util import DBUtil
from user_util import UserUtil


class MeArticlesDraftsShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')

        validate(self.event.get('pathParameters'), self.get_schema())

    def exec_main_proc(self):
        params = self.event.get('pathParameters')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_info = article_info_table.get_item(Key={'article_id': params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': params['article_id']}).get('Item')

        DBUtil.validate_article_existence(
            self.dynamodb,
            params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft'
        )

        if 'price' in article_info:
            article_content['body'] = article_content['paid_body']
            article_content.pop('paid_body', None)

        if article_content is not None:
            article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
