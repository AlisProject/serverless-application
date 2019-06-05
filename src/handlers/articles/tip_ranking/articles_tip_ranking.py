# -*- coding: utf-8 -*-
import json
import settings
from db_util import DBUtil
from es_util import ESUtil
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class ArticlesTipRanking(LambdaBase):
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
        limit = int(self.params['limit']) if self.params.get('limit') else settings.ARTICLES_TIP_RAKING_DEFAULT_LIMIT
        page = int(self.params['page']) if self.params.get('page') else 1

        articles = ESUtil.search_tip_ranked_articles(self.elasticsearch, self.params, limit, page)

        response = {
            'Items': articles
        }

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
