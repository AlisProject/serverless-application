# -*- coding: utf-8 -*-
import json
import os
import settings
import time

from botocore.exceptions import ClientError
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate


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
        validate(self.params, self.get_schema())
        DBUtil.validate_comment_existence(self.dynamodb, self.params['comment_id'])

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        comment_liked_user_table = self.dynamodb.Table(os.environ['COMMENT_LIKED_USER_TABLE_NAME'])

        comment = {
            'comment_id': self.params['comment_id'],
            'user_id': user_id,
            'created_at': int(time.time())
        }

        try:
            comment_liked_user_table.put_item(
                Item=comment,
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
