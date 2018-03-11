# -*- coding: utf-8 -*-
import os
import json
import logging
import traceback
import settings
from decimal import Decimal, ROUND_DOWN
import time
from jsonschema import validate, ValidationError, FormatChecker
from hashids import Hashids
from text_sanitizer import TextSanitizer


class ArticlesDraftCreate(object):
    def __init__(self, event, context, dynamodb):
        self.event = event
        self.context = context
        self.dynamodb = dynamodb
        self.sort_key = self.__generate_sort_key()
        self.article_id = self.__generate_article_id(self.sort_key)

    def main(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        schema = {
            'type': 'object',
            'properties': {
                'title': settings.parameters['title'],
                'body': settings.parameters['body'],
                'eye_catch_url': settings.parameters['eye_catch_url'],
                'overview': settings.parameters['overview']
            }
        }

        try:
            if self.event.get('body') is None:
                raise ValidationError('Request parameter is required')

            params = json.loads(self.event.get('body'))

            validate(params, schema, format_checker=FormatChecker())

            self.__create_article_info(params)
        except ValidationError as err:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Invalid parameter: {0}".format(err)})
            }
        except Exception as err:
            logger.fatal(err)
            traceback.print_exc()

            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

        try:
            self.__create_article_content(params)
        except Exception as err:
            logger.fatal(err)
            traceback.print_exc()
        finally:
            return {
                'statusCode': 200,
                'body': json.dumps({'article_id': self.article_id})
            }

    def __create_article_info(self, params):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info = {
            'article_id': self.article_id,
            'user_id': 'USER_ID',  # FIXME. Autorizationの実装が完了したらcognito経由でuser_idを取得する
            'status': 'draft',
            'title': TextSanitizer.sanitize_text(params.get('title')),
            'overview': TextSanitizer.sanitize_text(params.get('overview')),
            'eye_catch_url': params.get('eye_catch_url'),
            'sort_key': self.sort_key,
            'created_at': int(time.time())
        }

        article_info_table.put_item(Item=article_info)

    def __create_article_content(self, params):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_content = {
            'article_id': self.article_id,
            'body': TextSanitizer.sanitize_article_body(params.get('body')),
            'title': TextSanitizer.sanitize_text(params.get('title'))
        }

        article_content_table.put_item(Item=article_content)

    def __generate_article_id(self, target):
        hashids = Hashids(salt=os.environ['SALT_FOR_ARTICLE_ID'], min_length=settings.article_id_length)
        return hashids.encode(target)

    def __generate_sort_key(self):
        unixtime_now_decimal = time.time()
        return int(unixtime_now_decimal * (10 ** settings.sort_key_additional_digits_number))
