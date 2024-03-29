# -*- coding: utf-8 -*-
import logging
import os
import traceback

import settings
import time

from boto3.dynamodb.conditions import Key
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from db_util import DBUtil
from parameter_util import ParameterUtil
from tag_util import TagUtil
from time_util import TimeUtil
from user_util import UserUtil


class MeArticlesDraftsPublish(LambdaBase):
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
        UserUtil.verified_phone_and_email(self.event)
        if self.event['requestContext']['authorizer']['claims'].get('custom:private_eth_address') is None:
            raise ValidationError('not exists private_eth_address')

        validate(self.params, self.get_schema())

        if self.params.get('tags'):
            ParameterUtil.validate_array_unique(self.params['tags'], 'tags', case_insensitive=True)
            TagUtil.validate_tags(
                self.params['tags'],
                self.event['requestContext']['authorizer']['claims']['cognito:username']
            )

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft'
        )

        DBUtil.validate_topic(self.dynamodb, self.params['topic'])

    def exec_main_proc(self):
        self.__delete_article_content_edit()
        self.__create_article_history_and_update_sort_key()

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info_before = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression='set #attr = :article_status, sync_elasticsearch = :one, topic = :topic, tags = :tags',
            ExpressionAttributeNames={'#attr': 'status'},
            ExpressionAttributeValues={
                ':article_status': 'public',
                ':one': 1,
                ':topic': self.params['topic'],
                ':tags': TagUtil.get_tags_with_name_collation(self.elasticsearch, self.params.get('tags'))
            }
        )

        try:
            TagUtil.create_and_count(self.elasticsearch, article_info_before.get('tags'), self.params.get('tags'))
        except Exception as e:
            logging.fatal(e)
            traceback.print_exc()

        return {
            'statusCode': 200
        }

    def __delete_article_content_edit(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])
        article_content_edit = article_content_edit_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        if article_content_edit:
            article_content_edit_table.delete_item(Key={'article_id': self.params['article_id']})

    def __create_article_history_and_update_sort_key(self):
        # update sort_key
        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        article_histories = article_history_table.query(
            KeyConditionExpression=Key('article_id').eq(self.params['article_id'])
        )['Items']

        if len(article_histories) == 0:
            sort_key = TimeUtil.generate_sort_key()
            article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
            article_info_table.update_item(
                Key={
                    'article_id': self.params['article_id'],
                },
                UpdateExpression='set sort_key = :sort_key, published_at = :published_at',
                ExpressionAttributeValues={':sort_key': sort_key, ':published_at': int(time.time())}
            )

        # create article_history
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        article_content = article_content_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        article_history_table.put_item(
            Item={
                'article_id': article_content['article_id'],
                'title': article_content['title'],
                'body': article_content['body'],
                'created_at': int(time.time())
            }
        )
