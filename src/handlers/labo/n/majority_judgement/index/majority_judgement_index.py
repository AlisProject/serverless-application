# -*- coding: utf-8 -*-
import os
import json
from lambda_base import LambdaBase


class LaboNMajorityJudgementIndex(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        table = self.dynamodb.Table(os.environ['MAJORITY_JUDGEMENT_TABLE_NAME'])

        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        exists = LaboNMajorityJudgementIndex.__is_exists(table, user_id)

        return {
            'statusCode': 200,
            'body': json.dumps({'exists': exists})
        }

    @staticmethod
    def __is_exists(table, user_id):
        result = table.get_item(Key={'user_id': user_id}).get('Item')

        return False if result is None else True
