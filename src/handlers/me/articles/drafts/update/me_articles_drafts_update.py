# -*- coding: utf-8 -*-
import os
import json
import logging
import traceback
import settings
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError, FormatChecker
from text_sanitizer import TextSanitizer
from db_util import DBUtil


class MeArticlesDraftsUpdate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'title': settings.parameters['title'],
                'body': settings.parameters['body'],
                'eye_catch_url': settings.parameters['eye_catch_url'],
                'overview': settings.parameters['overview']
            }
        }

    def validate_params(self):
        if not self.event.get('pathParameters'):
            raise ValidationError('pathParameters is required')

        if not self.event.get('body') or not json.loads(self.event.get('body')):
            raise ValidationError('Request parameter is required')

        validate(self.event.get('pathParameters'), self.get_schema())
        validate(json.loads(self.event.get('body')), self.get_schema(), format_checker=FormatChecker())

    def exec_main_proc(self):
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.event['pathParameters']['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft'
        )

        params = json.loads(self.event.get('body'))

        self.__update_article_content(params)
        self.__update_article_info(params)

        return {
            'statusCode': 200
        }

    def __update_article_info(self, params):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info_table.update_item(
            Key={
                'article_id': self.event['pathParameters']['article_id'],
            },
            UpdateExpression="set title = :title, overview=:overview, eye_catch_url=:eye_catch_url",
            ExpressionAttributeValues={
                ':title': TextSanitizer.sanitize_text(params.get('title')),
                ':overview': TextSanitizer.sanitize_text(params.get('overview')),
                ':eye_catch_url': params.get('eye_catch_url')
            }
        )

    def __update_article_content(self, params):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_content_table.update_item(
            Key={
                'article_id': self.event['pathParameters']['article_id'],
            },
            UpdateExpression="set title = :title, body=:body",
            ExpressionAttributeValues={
                ':title': TextSanitizer.sanitize_text(params.get('title')),
                ':body': TextSanitizer.sanitize_article_body(params.get('body'))
            }
        )
