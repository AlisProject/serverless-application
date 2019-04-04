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
from user_util import UserUtil


class MeArticlesPublicRepublishWithHeader(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'topic': settings.parameters['topic'],
                'tags': settings.parameters['tags'],
                'eye_catch_url': settings.parameters['eye_catch_url'],
                'price': settings.parameters['price'],
                'paid_body': settings.parameters['paid_body']
            },
            'required': ['article_id', 'topic']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

        # check paid articles params required
        if (self.params.get('price') is not None and self.params.get('paid_body') is None) or \
           (self.params.get('price') is None and self.params.get('paid_body') is not None):
            raise ValidationError('Both paid body and price are required.')

        # check price type is integer or decimal
        ParameterUtil.validate_price_params(self.params.get('price'))
        self.params['price'] = int(self.params['price'])

        validate(self.params, self.get_schema())

        if self.params.get('tags'):
            ParameterUtil.validate_array_unique(self.params['tags'], 'tags', case_insensitive=True)
            TagUtil.validate_format(self.params['tags'])

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='public',
            version=2
        )

        DBUtil.validate_topic(self.dynamodb, self.params['topic'])

    def exec_main_proc(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])
        article_content_edit = article_content_edit_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info_before = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        self.__validate_article_content_edit(article_content_edit)

        self.__create_article_history(article_content_edit)

        # when price key exists in article_info but params has no price key
        if article_info_before.get('price') is not None and self.params.get('price') is None:
            self.__make_article_free(article_info_table, article_content_table)

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
        info_expression_attribute_values = {
            ':title': article_content_edit['title'],
            ':eye_catch_url': self.params.get('eye_catch_url'),
            ':one': 1,
            ':topic': self.params['topic'],
            ':tags': TagUtil.get_tags_with_name_collation(self.elasticsearch, self.params.get('tags'))
        }

        info_update_expression = 'set sync_elasticsearch = :one, topic = :topic, tags = ' \
                                 ':tags, eye_catch_url=:eye_catch_url, title = :title'

        if self.params.get('price') is not None:
            info_expression_attribute_values.update({
                ':price': self.params.get('price')
            })
            info_update_expression = info_update_expression + ', price = :price'

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression=info_update_expression,
            ExpressionAttributeValues=info_expression_attribute_values
        )

    def __update_article_content(self, article_content_edit):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        content_update_expression = "set title = :title, body=:body"
        content_expression_attribute_values = {
            ':title': article_content_edit['title'],
            ':body': article_content_edit['body']
        }

        # paid article case
        if self.params.get('price') is not None:
            content_update_expression = "set title = :title, body=:body, paid_body=:paid_body"
            content_expression_attribute_values.update({':paid_body': self.params['paid_body']})

        article_content_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression=content_update_expression,
            ExpressionAttributeValues=content_expression_attribute_values
        )

    def __create_article_history(self, article_content_edit):
        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        article_body = article_content_edit['body']
        if self.params.get('paid_body') is not None:
            article_body = self.params.get('paid_body')
        Item = {
            'article_id': article_content_edit['article_id'],
            'title': article_content_edit['title'],
            'body': article_body,
            'created_at': int(time.time())
        }
        if self.params.get('price') is not None:
            Item.update({'price': self.params.get('price')})
        article_history_table.put_item(
            Item=Item
        )

    def __validate_article_content_edit(self, article_content_edit):
        if article_content_edit is None:
            raise RecordNotFoundError('Record Not Found')

        required_params = ['title', 'body']

        for param in required_params:
            if not article_content_edit[param]:
                raise ValidationError("%s is required" % param)

    def __make_article_free(self, article_info_table, article_content_table):
        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression='REMOVE price'
        )

        article_content_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression='REMOVE paid_body'
        )
