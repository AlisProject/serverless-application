# -*- coding: utf-8 -*-
import os
import sys
import boto3
import json
import logging
import traceback
import settings
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder


class ArticlesShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        params = self.event.get('pathParameters')

        if params is None:
            raise ValidationError('pathParameters is required')

        validate(params, self.get_schema())

    def exec_main_proc(self):
        params = self.event.get('pathParameters')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_info = article_info_table.get_item(Key={'article_id': params['article_id']}).get('Item')
        article_content = article_content_table.get_item(Key={'article_id': params['article_id']}).get('Item')

        if article_info is None or article_content is None:
            return {
               'statusCode': 404,
               'body': json.dumps({'message': 'Record Not Found'})
            }

        article_info.update(article_content)

        return {
            'statusCode': 200,
            'body': json.dumps(article_info, cls=DecimalEncoder)
        }
