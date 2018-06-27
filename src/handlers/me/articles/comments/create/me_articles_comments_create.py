# -*- coding: utf-8 -*-
import os
import settings
import time

from db_util import DBUtil
from hashids import Hashids
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil
from text_sanitizer import TextSanitizer


class MeArticlesCommentsCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'text': settings.parameters['comment']['text']
            },
            'required': ['article_id', 'text']
        }

    def validate_params(self):
        if not self.event.get('body'):
            raise ValidationError('Request parameter is required')

        validate(self.params, self.get_schema())
        DBUtil.validate_article_existence(self.dynamodb, self.params['article_id'], status='public')


    def exec_main_proc(self):
        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        comment_id = self.__generate_comment_id(sort_key)

        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])

        comment = {
            'comment_id': comment_id,
            'article_id': self.params['article_id'],
            'text': TextSanitizer.sanitize_text(self.params['text']),
            'user_id': user_id,
            'sort_key': sort_key,
            'created_at': int(time.time())
        }

        comment_table.put_item(
            Item=comment,
            ConditionExpression='attribute_not_exists(comment_id)'
        )

        return {'statusCode': 200}

    def __generate_comment_id(self, target):
        hashids = Hashids(salt=os.environ['SALT_FOR_ARTICLE_ID'], min_length=settings.COMMENT_ID_LENGTH)
        return hashids.encode(target)
