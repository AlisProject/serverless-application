# -*- coding: utf-8 -*-
import os
import json
import settings
from user_util import UserUtil
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from db_util import DBUtil


class MeArticlesPublicEdit(LambdaBase):
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

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='public'
        )

    def exec_main_proc(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])

        article_content_edit = article_content_edit_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        if article_content_edit:
            article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
            article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
            article_info.update(article_content_edit)
            return_value = article_info
        else:
            article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
            article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

            article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
            article_content = article_content_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

            if 'price' in article_info:
                article_content['body'] = article_content['paid_body']
                article_content.pop('paid_body', None)

            article_info.update(article_content)

            return_value = article_info

        # version が指定されていた場合は、指定の version で body を上書き
        if self.params.get('version') is not None:
            article_content_edit_history = DBUtil.get_article_content_edit_history(
                self.dynamodb,
                self.event['requestContext']['authorizer']['claims']['cognito:username'],
                self.params['article_id'],
                self.params['version']
            )
            return_value['body'] = article_content_edit_history.get('body')

        return {
            'statusCode': 200,
            'body': json.dumps(return_value, cls=DecimalEncoder)
        }
