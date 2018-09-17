# -*- coding: utf-8 -*-
import logging
import os
import time
import traceback

import settings
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from db_util import DBUtil
from parameter_util import ParameterUtil
from record_not_found_error import RecordNotFoundError
from tag_util import TagUtil


class MeArticlesPublicRepublish(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'topic': settings.parameters['topic'],
                'tags': settings.parameters['tags']
            },
            'required': ['article_id', 'topic']
        }

    def validate_params(self):
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')

        validate(self.params, self.get_schema())

        if self.params.get('tags'):
            ParameterUtil.validate_array_unique(self.params['tags'], 'tags', case_insensitive=True)
            TagUtil.validate_format(self.params['tags'])

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='public'
        )

        DBUtil.validate_topic(self.dynamodb, self.params['topic'])

    def exec_main_proc(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])
        article_content_edit = article_content_edit_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info_before = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        self.__validate_article_content_edit(article_content_edit)

        self.__create_article_history(article_content_edit)
        self.__update_article_info(article_content_edit)
        self.__update_article_content(article_content_edit)

        article_content_edit_table.delete_item(Key={'article_id': self.params['article_id']})

        try:
            TagUtil.create_and_count(self.elasticsearch, article_info_before.get('tags'), self.params.get('tags'))
        except Exception as e:
            logging.fatal(e)
            traceback.print_exc()

        return {
            'statusCode': 200
        }

    def __update_article_info(self, article_content_edit):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression=("set title = :title, overview=:overview, eye_catch_url=:eye_catch_url, "
                              "sync_elasticsearch=:sync_elasticsearch, topic=:topic, tags=:tags"),
            ExpressionAttributeValues={
                ':title': article_content_edit['title'],
                ':overview': article_content_edit['overview'],
                ':eye_catch_url': article_content_edit['eye_catch_url'],
                ':sync_elasticsearch': 1,
                ':topic': self.params['topic'],
                ':tags': TagUtil.get_tags_with_name_collation(self.elasticsearch, self.params.get('tags'))
            }
        )

    def __update_article_content(self, article_content_edit):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_content_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression="set title = :title, body=:body",
            ExpressionAttributeValues={
                ':title': article_content_edit['title'],
                ':body': article_content_edit['body']
            }
        )

    def __create_article_history(self, article_content_edit):
        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        article_history_table.put_item(
            Item={
                'article_id': article_content_edit['article_id'],
                'title': article_content_edit['title'],
                'body': article_content_edit['body'],
                'created_at': int(time.time())
            }
        )

    def __validate_article_content_edit(self, article_content_edit):
        if article_content_edit is None:
            raise RecordNotFoundError('Record Not Found')

        required_params = ['title', 'body', 'overview']

        for param in required_params:
            if not article_content_edit[param]:
                raise ValidationError("%s is required" % param)
