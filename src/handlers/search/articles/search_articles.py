# -*- coding: utf-8 -*-
import json
from es_util import ESUtil
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder


class SearchArticles(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'required': ['search']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        response = ESUtil.search_article(self.elasticsearch, self.params['search'])
        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
