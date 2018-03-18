# -*- coding: utf-8 -*-
import os
import sys
import boto3
import json
import logging
import traceback
import settings
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder


class ArticlesShow(object):
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
