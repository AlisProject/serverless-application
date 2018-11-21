# -*- coding: utf-8 -*-
import json
import os
import settings
import time

from botocore.exceptions import ClientError
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate
from user_util import UserUtil


class MeCommentsLikesCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'comment_id': settings.parameters['comment']['comment_id']
            },
            'required': ['comment_id']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema())
        comment = DBUtil.get_validated_comment(self.dynamodb, self.params['comment_id'])
        DBUtil.validate_article_existence(self.dynamodb, comment['article_id'], status='public')

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        comment = comment_table.get_item(Key={'comment_id': self.params['comment_id']}).get('Item')

        comment_liked_user_table = self.dynamodb.Table(os.environ['COMMENT_LIKED_USER_TABLE_NAME'])
        comment_liked_user = {
            'comment_id': comment['comment_id'],
            'user_id': user_id,
            'article_id': comment['article_id'],
            'created_at': int(time.time())
        }

        try:
            comment_liked_user_table.put_item(
                Item=comment_liked_user,
                ConditionExpression='attribute_not_exists(comment_id)'
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'Already exists'})
                }
            else:
                raise

        return {'statusCode': 200}
