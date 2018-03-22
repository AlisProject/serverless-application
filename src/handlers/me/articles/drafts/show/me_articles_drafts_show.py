# -*- coding: utf-8 -*-
import os
import boto3
import json
import logging
import traceback
import settings
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder


class MeArticlesDraftsShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')

        validate(self.event.get('pathParameters'), self.get_schema())

    def exec_main_proc(self):
        params = self.event.get('pathParameters')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_info = article_info_table.get_item(Key={'article_id': params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': params['article_id']}).get('Item')

        if article_info is None or article_info['status'] != 'draft':
            return {
               'statusCode': 404,
               'body': json.dumps({'message': 'Record Not Found'})
            }

        if article_info['user_id'] != self.event['requestContext']['authorizer']['claims']['cognito:username']:
            return {
               'statusCode': 403,
               'body': json.dumps({'message': 'Forbidden'})
            }

        if article_content is not None:
            article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
