# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from db_util import DBUtil
from user_util import UserUtil


class MeArticlesDraftsShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'version': settings.parameters['article_content_edit_history_version']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema())

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

        # version が指定されていた場合は、指定の version で body を上書き
        if self.params.get('version') is not None:
            article_content_edit_history = DBUtil.get_article_content_edit_history(
                self.dynamodb,
                self.event['requestContext']['authorizer']['claims']['cognito:username'],
                self.params['article_id'],
                self.params['version']
            )
            article_content['body'] = article_content_edit_history.get('body')

        if article_content is not None:
            article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
