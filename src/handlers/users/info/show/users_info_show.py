# -*- coding: utf-8 -*-
import json
import os
import settings
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from record_not_found_error import RecordNotFoundError


class UsersInfoShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_id': settings.parameters['user_id'],
            },
            'required': ['user_id']
        }

    def validate_params(self):
        # single
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        response = users_table.get_item(Key={'user_id': self.params['user_id']})

        if response.get('Item') is None:
            raise RecordNotFoundError('Record Not Found')

        return {
            'statusCode': 200,
            'body': json.dumps(response['Item'], cls=DecimalEncoder)
        }
