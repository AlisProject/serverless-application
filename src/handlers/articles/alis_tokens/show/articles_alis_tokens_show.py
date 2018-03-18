# -*- coding: utf-8 -*-
import os
import sys
import boto3
import json
import logging
import decimal
import traceback
import settings
from lambda_base import LambdaBase
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class ArticlesAlisTokensShow(LambdaBase):
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
        article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
        article_alis_token_table = self.dynamodb.Table(os.environ['ARTICLE_ALIS_TOKEN_TABLE_NAME'])

        active_evaluated_at = article_evaluated_manage_table.scan()['Items'][0]['active_evaluated_at']

        responce = article_alis_token_table.get_item(
            Key={
                'evaluated_at': active_evaluated_at,
                'article_id': self.event['pathParameters']['article_id']
            }
        )

        if responce.get('Item') is None:
            return {
               'statusCode': 404,
               'body': json.dumps({'message': 'Record Not Found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(responce['Item'], cls=DecimalEncoder)
        }
