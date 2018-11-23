import json
import math
import os

from jsonschema import validate

import settings
from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from parameter_util import ParameterUtil


class ArticlesRecommended(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit'],
                'page': settings.parameters['page']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())

        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        recommended_article_ids = self.__get_screened_article_ids('recommended')

        excluded_article_ids = self.__get_screened_article_ids('eyecatch') + self.__get_screened_article_ids('blacklisted')
        recommended_article_ids = [
            article_id for article_id in recommended_article_ids if article_id not in excluded_article_ids
        ]

        articles = self.__get_public_articles_from_ids(recommended_article_ids)

        pagenated_articles = self.__get_pagenated_items(articles)

        return {
            'statusCode': 200,
            'body': json.dumps({'Items': pagenated_articles}, cls=DecimalEncoder)
        }

    def __get_pagenated_items(self, items):
        limit = int(self.params['limit']) if self.params.get('limit') else settings.ARTICLES_RECOMMENDED_DEFAULT_LIMIT
        page = int(self.params['page']) if self.params.get('page') else 1

        start = (page - 1) * limit
        end = start + limit

        return items[start:end]

    def __get_screened_article_ids(self, article_type):
        screened_article_table = self.dynamodb.Table(os.environ['SCREENED_ARTICLE_TABLE_NAME'])
        screened_article = screened_article_table.get_item(Key={'article_type': article_type}).get('Item')

        if not screened_article or not screened_article.get('articles'):
            return []

        return screened_article['articles']

    def __get_public_articles_from_ids(self, target_article_ids):
        if not target_article_ids:
            return []

        article_info_table_name = os.environ['ARTICLE_INFO_TABLE_NAME']

        # batch_get_itemが100件よりも多い件数を扱うとエラーになるため100件ごと区切って処理する
        split_num = math.floor(len(target_article_ids) / settings.DYNAMO_BATCH_GET_MAX)
        if not len(target_article_ids) % settings.DYNAMO_BATCH_GET_MAX == 0:
            split_num += 1

        split_article_ids = [
            target_article_ids[index*settings.DYNAMO_BATCH_GET_MAX:(index+1)*settings.DYNAMO_BATCH_GET_MAX]
            for index
            in range(split_num)
        ]

        public_articles = []

        for article_ids in split_article_ids:
            response = self.dynamodb.batch_get_item(
                RequestItems={
                    article_info_table_name: {
                        'Keys': [{'article_id': article_id} for article_id in article_ids]
                    }
                }
            )
            articles = response['Responses'][article_info_table_name]
            public_articles.extend([article for article in articles if article['status'] == 'public'])

        # dynamodbのbatch_get_itemsは順序が保証されないため、target_article_idsを駆動表にして順序を並べなおす
        articles = {}
        for article in public_articles:
            articles[article['article_id']] = article

        result = [articles[article_id] for article_id in target_article_ids if articles.get(article_id)]

        return result
