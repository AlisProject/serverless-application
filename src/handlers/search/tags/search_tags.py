import json

from jsonschema import validate

import settings
from decimal_encoder import DecimalEncoder
from es_util import ESUtil
from lambda_base import LambdaBase


class SearchTags(LambdaBase):
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
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        query = self.params['query']
        limit = int(self.params.get('limit')) if self.params.get('limit') is not None else settings.TAG_SEARCH_DEFAULT_LIMIT
        page = int(self.params.get('page')) if self.params.get('page') is not None else 1

        result = ESUtil.search_tag(self.elasticsearch, query, limit, page)
        return {
            'statusCode': 200,
            'body': json.dumps(result, cls=DecimalEncoder)
        }
