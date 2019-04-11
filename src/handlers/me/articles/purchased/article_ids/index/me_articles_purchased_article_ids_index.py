# -*- coding: utf-8 -*-
import json
import os

from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from lambda_base import LambdaBase


class MeArticlesPurchasedArticleIdsIndex(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])

        query_params = {
            'IndexName': 'user_id-sort_key-index',
            'KeyConditionExpression': Key('user_id').eq(user_id)
        }

        result = DBUtil.query_all_items(paid_articles_table, query_params)

        article_ids = [paid_article['article_id'] for paid_article in result if
                       paid_article['user_id'] == user_id and paid_article['status'] == 'done']

        return {
            'statusCode': 200,
            'body': json.dumps({'article_ids': article_ids})
        }
