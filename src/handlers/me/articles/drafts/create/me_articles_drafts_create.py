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
from db_util import DBUtil
from user_util import UserUtil


class MeArticlesDraftsCreate(LambdaBase):
    def get_schema(self):
        params = json.loads(self.event['body'])
        if 'version' in params and params['version'] is 200:
            return {
                'type': 'object',
                'properties': {
                    'title': settings.parameters['title'],
                    'eye_catch_url': settings.parameters['eye_catch_url'],
                    'overview': settings.parameters['overview'],
                    'body': {
                        'type': 'array'
                    }
                }
            }
        else:
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
        UserUtil.verified_phone_and_email(self.event)
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

        if 'version' in params:
            article_info['version'] = params['version']
        DBUtil.items_values_empty_to_none(article_info)

        article_info_table.put_item(
            Item=article_info,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __create_article_content(self, params, article_id):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        if 'version' in params and params['version'] is 200:
            article_content = {
                'article_id': article_id,
                'body': TextSanitizer.sanitize_article_object(params.get('body')),
                'title': TextSanitizer.sanitize_text(params.get('title')),
                'created_at': int(time.time()),
                'version': params['version']
            }
        else:
            article_content = {
                'article_id': article_id,
                'body': TextSanitizer.sanitize_article_body(params.get('body')),
                'title': TextSanitizer.sanitize_text(params.get('title')),
                'created_at': int(time.time())
            }

        DBUtil.items_values_empty_to_none(article_content)

        article_content_table.put_item(
            Item=article_content,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __generate_article_id(self, target):
        hashids = Hashids(salt=os.environ['SALT_FOR_ARTICLE_ID'], min_length=settings.article_id_length)
        return hashids.encode(target)
