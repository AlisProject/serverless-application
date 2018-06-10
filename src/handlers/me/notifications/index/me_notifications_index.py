# -*- coding: utf-8 -*-
import os
import settings
import json
from decimal_encoder import DecimalEncoder
from boto3.dynamodb.conditions import Key
from parameter_util import ParameterUtil
from lambda_base import LambdaBase
from jsonschema import validate


class MeNotificationsIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit'],
                'sort_key': settings.parameters['sort_key']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        limit = settings.NOTIFICATION_INDEX_DEFAULT_LIMIT
        if self.params.get('limit'):
            limit = int(self.params.get('limit'))

        query_params = {
            'Limit': limit,
            'IndexName': 'user_id-sort_key-index',
            'KeyConditionExpression': Key('user_id').eq(user_id),
            'ScanIndexForward': False
        }

        if self.params.get('notification_id') is not None and self.params.get('sort_key') is not None:
            LastEvaluatedKey = {
                'notification_id': self.params.get('notification_id'),
                'user_id': user_id,
                'sort_key': int(self.params['sort_key'])
            }

            query_params.update({'ExclusiveStartKey': LastEvaluatedKey})

        response = notification_table.query(**query_params)

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
