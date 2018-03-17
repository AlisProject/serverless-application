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


class ArticleInfoRecent(object):
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
                'limit': settings.parameters['limit'],
                'article_id': settings.parameters['article_id'],
                'sort_key': settings.parameters['sort_key']
            }
        }

        try:
            params = self.event.get('queryStringParameters')
            if params is None:
                raise ValidationError('queryStringParameters is required')

            ParameterUtil.cast_parameter_to_int(params, schema)
            validate(params, schema)

            dynamo_tbl = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

            limit = int(params.get('limit')) if params.get('limit') is not None else settings.article_recent_default_limit

            query_params = {
                'Limit': limit,
                'IndexName': 'status-sort_key-index',
                'KeyConditionExpression': Key('status').eq('public'),
                'ScanIndexForward': False
            }

            if params.get('article_id') is not None and params.get('sort_key') is not None:
                LastEvaluatedKey = {
                    'status': 'public',
                    'article_id': params.get('article_id'),
                    'sort_key': params.get('sort_key')
                }

                query_params.update({'ExclusiveStartKey': LastEvaluatedKey})

            responce = dynamo_tbl.query(**query_params)

            return {
                'statusCode': 200,
                'body': json.dumps(responce, cls=DecimalEncoder)
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
