# -*- coding: utf-8 -*-
import os
from lambda_base import LambdaBase


class LaboNMajorityJudgementDeleteAll(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        table = self.dynamodb.Table(os.environ['MAJORITY_JUDGEMENT_TABLE_NAME'])

        LaboNMajorityJudgementDeleteAll.truncate_dynamo_items(table)

        return True

    @staticmethod
    def truncate_dynamo_items(dynamodb_table):
        delete_items = []
        parameters = {}
        while True:
            response = dynamodb_table.scan(**parameters)
            delete_items.extend(response["Items"])
            if ("LastEvaluatedKey" in response):
                parameters["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            else:
                break

        key_names = [x["AttributeName"] for x in dynamodb_table.key_schema]
        delete_keys = [{k: v for k, v in x.items() if k in key_names} for x in delete_items]

        with dynamodb_table.batch_writer() as batch:
            for key in delete_keys:
                batch.delete_item(Key=key)

        return 0
