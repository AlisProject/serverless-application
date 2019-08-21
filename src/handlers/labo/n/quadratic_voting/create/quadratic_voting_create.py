# -*- coding: utf-8 -*-
import os
import time
import math
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError

options_count = 6  # 選択肢の数
credit_per_user = 100  # ユーザに付与されるクレジット(持ち越しは考慮しない)
maximum = math.sqrt(credit_per_user)  # 許容される最大の値


class LaboNQuadraticVotingCreate(LambdaBase):
    def get_schema(self):
        opt = {
            "type": "integer",
            "minimum": 0,
            "maximum": maximum
        }

        required = []
        properties = {}
        for i in range(options_count):
            key = 'opt_' + str(i + 1)
            properties[key] = opt
            required.append(key)

        for i in range(options_count):
            properties['opt_' + str(i + 1)] = opt

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

        totalVotedValue = 0
        for key in self.params:
            totalVotedValue += self.params[key] ** 2

        # 投票の合計がCreditの限界を超えている場合
        if totalVotedValue > credit_per_user:
            raise ValidationError('Invalid')

    def exec_main_proc(self):
        table = self.dynamodb.Table(os.environ['QUADRATIC_VOTING_TABLE_NAME'])

        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        if not LaboNQuadraticVotingCreate.__is_exists(table, user_id):
            item = {
                'user_id': user_id,
                'created_at': int(time.time())
            }

            for key, value in self.params.items():
                item[key] = value

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
