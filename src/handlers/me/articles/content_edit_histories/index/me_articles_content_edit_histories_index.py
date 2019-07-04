# -*- coding: utf-8 -*-
import os
import json
import settings
from boto3.dynamodb.conditions import Key
from lambda_base import LambdaBase
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from user_util import UserUtil
from db_util import DBUtil


class MeArticlesContentEditHistoriesIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema())
        # 該当 article_id が自分のものかつ、v2であることを確認
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            version=2
        )

    def exec_main_proc(self):
        article_content_edit_history_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'])

        # article_id-sort_key-index は射影に body を含めておらず 1MB を超えないため、LastEvaluatedKey の確認は不要
        query_params = {
            'IndexName': 'article_id-sort_key-index',
            'KeyConditionExpression': Key('article_id').eq(self.params['article_id']),
            'ScanIndexForward': False
        }
        response = article_content_edit_history_table.query(**query_params)

        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder)
        }
