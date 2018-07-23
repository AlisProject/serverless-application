# -*- coding: utf-8 -*-
import json
import os
import settings

from boto3.dynamodb.conditions import Key
from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from jsonschema import validate


class CommentsLikesShow(LambdaBase):
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

    def exec_main_proc(self):
        comment_liked_user_table = self.dynamodb.Table(os.environ['COMMENT_LIKED_USER_TABLE_NAME'])

        query_params = {
            'KeyConditionExpression': Key('comment_id').eq(self.event['pathParameters']['comment_id']),
            'Select': 'COUNT'
        }

        response = comment_liked_user_table.query(**query_params)

        return {
            'statusCode': 200,
            'body': json.dumps({'count': response['Count']}, cls=DecimalEncoder)
        }
