# -*- coding: utf-8 -*-
import json
import settings
from es_util import ESUtil
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class SearchUsers(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit'],
                'page': settings.parameters['page'],
                'query': settings.parameters['query']
            },
            'required': ['query']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

    # TODO: LINE_とTwitter_で検索をかけられた場合、データを弾く処理追加
    def exec_main_proc(self):
        query = self.params['query']
        limit = int(self.params.get('limit')) if self.params.get('limit') is not None else settings.article_recent_default_limit
        page = int(self.params.get('page')) if self.params.get('page') is not None else 1
        response = ESUtil.search_user(self.elasticsearch, query, limit, page)
        result = []
        for u in response["hits"]["hits"]:
            result.append(u["_source"])
        return {
            'statusCode': 200,
            'body': json.dumps(result, cls=DecimalEncoder)
        }
