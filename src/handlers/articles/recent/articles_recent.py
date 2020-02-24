# -*- coding: utf-8 -*-
import json
import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil
from es_util import ESUtil


class ArticlesRecent(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit'],
                'page': settings.parameters['page'],
                'topic': settings.parameters['topic']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())

        validate(self.params, self.get_schema())

        if self.params.get('topic'):
            DBUtil.validate_topic(self.dynamodb, self.params['topic'])

    def exec_main_proc(self):
        limit = int(self.params.get('limit')) if self.params.get('limit') is not None \
            else settings.article_recent_default_limit
        page = int(self.params.get('page')) if self.params.get('page') is not None else 1

        articles = ESUtil.search_recent_articles(self.elasticsearch, self.dynamodb, self.params, limit, page)

        response = {
            'Items': articles
        }

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
