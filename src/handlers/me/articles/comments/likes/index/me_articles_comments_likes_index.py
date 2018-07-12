# -*- coding: utf-8 -*-
import json
import os
import settings

from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate


class MeArticlesCommentsLikesIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())
        DBUtil.validate_article_existence(self.dynamodb, self.params['article_id'], status='public')

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        comment_liked_user_table = self.dynamodb.Table(os.environ['COMMENT_LIKED_USER_TABLE_NAME'])

        query_params = {
            'IndexName': 'article_id-index',
            'KeyConditionExpression': Key('article_id').eq(self.params['article_id']),
        }

        result = DBUtil.query_all_items(comment_liked_user_table, query_params)

        comment_ids = [liked_user['comment_id'] for liked_user in result if liked_user['user_id'] == user_id]

        return {
            'statusCode': 200,
            'body': json.dumps({'comment_ids': comment_ids})
        }
