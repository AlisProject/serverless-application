# -*- coding: utf-8 -*-
import os
import time
from lambda_base import LambdaBase
from jsonschema import validate


class LaboMajorityJudgement(LambdaBase):
    def get_schema(self):
        opt = {
            "type": "number",
            "minimum": 1,
            "maximum": 5
        }

        return {
            "type": "object",
            "properties": {
                "opt_1": opt,
                "opt_2": opt,
                "opt_3": opt,
            },
            "required": ["opt_1", "opt_2", "opt_3"]
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        table = self.dynamodb.Table(os.environ['MAJORITY_JUDGEMENT_TABLE_NAME'])

        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        if not LaboMajorityJudgement.__is_exists(table, user_id):
            item = {
                'user_id': user_id,
                'opt_1': 5,
                'opt_2': 2,
                'opt_3': 3,
                'created_at': int(time.time())
            }

            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(user_id)'
            )

        return {
            'statusCode': 200
        }

    @staticmethod
    def __is_exists(table, user_id):
        result = table.get_item(Key={'user_id': user_id}).get('Item')

        return False if result is None else True
