# -*- coding: utf-8 -*-
import json
import os
from lambda_base import LambdaBase
from decimal_encoder import DecimalEncoder
from record_not_found_error import RecordNotFoundError


class MeInfoShow(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])

        response = users_table.get_item(Key={'user_id': user_id})

        if response.get('Item') is None:
            raise RecordNotFoundError('Record Not Found')

        return {
            'statusCode': 200,
            'body': json.dumps(response['Item'], cls=DecimalEncoder)
        }
