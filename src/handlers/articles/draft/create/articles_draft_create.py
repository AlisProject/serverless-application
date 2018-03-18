# -*- coding: utf-8 -*-
import os
import json
import logging
import traceback
import settings
import time
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError, FormatChecker
from hashids import Hashids
from text_sanitizer import TextSanitizer
from time_util import TimeUtil


class ArticlesDraftCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'title': settings.parameters['title'],
                'body': settings.parameters['body'],
                'eye_catch_url': settings.parameters['eye_catch_url'],
                'overview': settings.parameters['overview']
            }
        }

    def validate_params(self):
        if self.event.get('body') is None:
            raise ValidationError('Request parameter is required')

        params = json.loads(self.event.get('body'))

        validate(params, self.get_schema(), format_checker=FormatChecker())

    def exec_main_proc(self):
        sort_key = TimeUtil.generate_sort_key()
        article_id = self.__generate_article_id(sort_key)
        params = json.loads(self.event.get('body'))

        try:
            self.__create_article_info(params, sort_key, article_id)

            try:
                self.__create_article_content(params, article_id)
            except Exception as err:
                logging.fatal(err)
                traceback.print_exc()
            finally:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'article_id': article_id})
                }
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'Already exists'})
                }
            else:
                raise

    def __create_article_info(self, params, sort_key, article_id):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info = {
            'article_id': article_id,
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'status': 'draft',
            'title': TextSanitizer.sanitize_text(params.get('title')),
            'overview': TextSanitizer.sanitize_text(params.get('overview')),
            'eye_catch_url': params.get('eye_catch_url'),
            'sort_key': sort_key,
            'created_at': int(time.time())
        }

        article_info_table.put_item(
            Item=article_info,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __create_article_content(self, params, article_id):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_content = {
            'article_id': article_id,
            'body': TextSanitizer.sanitize_article_body(params.get('body')),
            'title': TextSanitizer.sanitize_text(params.get('title')),
            'created_at': int(time.time())
        }

        article_content_table.put_item(
            Item=article_content,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __generate_article_id(self, target):
        hashids = Hashids(salt=os.environ['SALT_FOR_ARTICLE_ID'], min_length=settings.article_id_length)
        return hashids.encode(target)
