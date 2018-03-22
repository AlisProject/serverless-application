# -*- coding: utf-8 -*-
import os
import settings
import json
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from boto3.dynamodb.conditions import Key


class MeArticleLikeShow(LambdaBase):
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
        article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])

        responce = article_liked_user_table.get_item(
            Key={
                'article_id': self.event['pathParameters']['article_id'],
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username']
            }
        )

        liked = True if responce.get('Item') is not None else False

        return {
            'statusCode': 200,
            'body': json.dumps({'liked': liked})
        }
