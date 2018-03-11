# -*- coding: utf-8 -*-
import os
import sys
import boto3
import json
import logging
import decimal
import traceback
import settings
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class ArticleAlisTokenShow(object):
    def __init__(self, event, context, dynamodb):
        self.event = event
        self.context = context
        self.dynamodb = dynamodb

    def main(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        schema = {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

        try:
            params = self.event.get('pathParameters')
            if params is None:
                raise ValidationError('pathParameters is required')

            validate(params, schema)

            article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
            article_alis_token_table = self.dynamodb.Table(os.environ['ARTICLE_ALIS_TOKEN_TABLE_NAME'])

            active_evaluated_at = article_evaluated_manage_table.scan()['Items'][0]['active_evaluated_at']

            responce = article_alis_token_table.get_item(
                Key={
                    'evaluated_at': active_evaluated_at,
                    'article_id': params['article_id']
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

        except ValidationError as err:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Invalid parameter: {0}".format(err)})
            }

        except Exception as err:
            logger.fatal(err)
            traceback.print_exc()

            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }
