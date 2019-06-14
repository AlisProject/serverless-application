# -*- coding: utf-8 -*-
import os
import time
import json
from es_util import ESUtil
from lambda_base import LambdaBase
from decimal_encoder import DecimalEncoder


class LaboMajorityJudgement(LambdaBase):
    # FIXME:
    def get_schema(self):
        pass

    # FIXME:
    def validate_params(self):
        pass

    def exec_main_proc(self):
        # article_id = self.__get_random_article()

        table = self.dynamodb.Table(os.environ['MAJORITY_JUDGEMENT_TABLE_NAME'])

        user_id = 'foobar'
        if not LaboMajorityJudgement.__is_exists(table, user_id):
            item = {
                'user_id': 'foobar',
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

    # def __get_random_article(self):
    #     response = ESUtil.search_random_article(self.elasticsearch)
    #
    #     article_id = response["hits"]["hits"][0]['_id']
    #
    #     return article_id

    @staticmethod
    def __is_exists(table, user_id):
        result = table.get_item(Key={'user_id': user_id}).get('Item')

        return False if result is None else True
