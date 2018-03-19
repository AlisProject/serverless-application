# -*- coding: utf-8 -*-
import os
import settings
import time
import json
from db_util import DBUtil
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil


class ArticlesLikesPost(LambdaBase):
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
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')
        validate(self.event.get('pathParameters'), self.get_schema())
        # relation
        if DBUtil.exists_public_article(self.dynamodb, self.event['pathParameters']['article_id']) is False:
            raise ValidationError('Bad Request')

    def exec_main_proc(self):
        try:
            article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
            self.__create_article_liked_user(article_liked_user_table)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'Already exists'})
                }
            else:
                raise

        return {
            'statusCode': 200
        }

    def __create_article_liked_user(self, article_liked_user_table):
        article_liked_user = {
            'article_id': self.event['pathParameters']['article_id'],
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'created_at': int(time.time()),
            'sort_key': TimeUtil.generate_sort_key()
        }
        article_liked_user_table.put_item(
            Item=article_liked_user,
            ConditionExpression='attribute_not_exists(article_id)'
        )
