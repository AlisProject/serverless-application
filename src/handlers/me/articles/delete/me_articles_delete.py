# -*- coding: utf-8 -*-
import os
import time
import settings
import logging
import json
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate
from user_util import UserUtil
from botocore.exceptions import ClientError


class MeArticlesDelete(LambdaBase):
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
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft')
        DBUtil.validate_article_history_existence(self.dynamodb, self.params['article_id'])

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(
            Key={"article_id": self.params['article_id']}
        )['Item']

        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        article_content = article_content_table.get_item(
            Key={"article_id": self.params['article_id']}
        )['Item']

        deleted_draft_article_info_table = self.dynamodb.Table(os.environ['DELETED_DRAFT_ARTICLE_INFO_TABLE_NAME'])
        deleted_draft_article_content_table = \
            self.dynamodb.Table(os.environ['DELETED_DRAFT_ARTICLE_CONTENT_TABLE_NAME'])

        article_info.update({'deleted_at': int(time.time())})
        article_content.update({'deleted_at': int(time.time())})

        try:
            deleted_draft_article_info_table.put_item(Item=article_info)
            deleted_draft_article_content_table.put_item(Item=article_content)
            article_info_table.delete_item(
                    Key={
                        'article_id': self.params['article_id']
                    }
            )
            article_content_table.delete_item(
                    Key={
                        'article_id': self.params['article_id']
                    }
            )
        except ClientError as e:
            logging.fatal(e)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

        return {'statusCode': 200}
