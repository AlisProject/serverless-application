# -*- coding: utf-8 -*-
import os
import time
import settings
from lambda_base import LambdaBase
from jsonschema import validate
from db_util import DBUtil


class MeArticlesPublicUnpublish(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
            },
            'required': ['article_id']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='public'
        )

    def exec_main_proc(self):
        self.__delete_article_content_edit()

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression='set #attr = :article_status, #sync_elasticsearch = :zero, #updated_at = :unixtime',
            ExpressionAttributeNames={
                '#attr': 'status',
                '#sync_elasticsearch': 'sync_elasticsearch',
                '#updated_at': 'updated_at'
            },
            ExpressionAttributeValues={':article_status': 'draft', ':zero': 0, ':unixtime': int(time.time())}
        )

        return {
            'statusCode': 200
        }

    def __delete_article_content_edit(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])
        article_content_edit = article_content_edit_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        if article_content_edit:
            article_content_edit_table.delete_item(Key={'article_id': self.params['article_id']})
