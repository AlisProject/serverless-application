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
        articles_purchased_table = self.dynamodb.Table(os.environ['ARTICLES_PURCHASED_TABLE_NAME'])

        query_params = {
            'IndexName': 'user_id-sort_key-index',
            'KeyConditionExpression': Key('user_id').eq(user_id)
        }

        result = DBUtil.query_all_items(articles_purchased_table, query_params)

        article_ids = [article_purchased['article_id'] for article_purchased in result if
                       article_purchased['user_id'] == user_id]

        return {
            'statusCode': 200,
            'body': json.dumps({'article_ids': article_ids})
        }
