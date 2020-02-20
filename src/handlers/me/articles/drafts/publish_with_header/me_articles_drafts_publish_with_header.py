# -*- coding: utf-8 -*-
import logging
import os
import traceback

import settings
import time

from boto3.dynamodb.conditions import Key
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from text_sanitizer import TextSanitizer
from db_util import DBUtil
from parameter_util import ParameterUtil
from tag_util import TagUtil
from time_util import TimeUtil
from user_util import UserUtil


class MeArticlesDraftsPublishWithHeader(LambdaBase):
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

        # check price type is integer or decimal
        ParameterUtil.validate_price_params(self.params.get('price'))
        if self.params.get('price') is not None:
            self.params['price'] = int(self.params['price'])

        validate(self.params, self.get_schema())

        if self.params.get('eye_catch_url'):
            TextSanitizer.validate_img_url(self.params.get('eye_catch_url'))

        if self.params.get('tags'):
            ParameterUtil.validate_array_unique(self.params['tags'], 'tags', case_insensitive=True)
            TagUtil.validate_format(self.params['tags'])

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft',
            version=2
        )

        DBUtil.validate_topic(self.dynamodb, self.params['topic'])

        DBUtil.validate_exists_title_and_body(self.dynamodb, self.params['article_id'])

    def exec_main_proc(self):
        # 公開する記事が有料設定か無料設定かの判定
        if self.params.get('price') is not None and self.params.get('paid_body') is not None:
            is_priced = True
        elif self.params.get('price') is None and self.params.get('paid_body') is None:
            is_priced = False
        else:
            raise ValidationError('Both paid body and price are required.')

        # 共通処理
        self.__delete_article_content_edit()
        self.__create_article_history_and_update_sort_key()

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info_before = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        # 有料記事の場合
        if is_priced:
            self.__update_paid_body(article_content_table)
            self.__update_paid_article_info(article_info_table)
        # 無料記事の場合
        else:
            # 有料記事から無料記事にする場合のみを考慮している
            self.__remove_price_and_paid_body(article_info_table, article_content_table)
            self.__update_article_info(article_info_table)

        try:
            TagUtil.create_and_count(self.elasticsearch, article_info_before.get('tags'), self.params.get('tags'))
        except Exception as e:
            logging.fatal(e)
            traceback.print_exc()

        return {
            'statusCode': 200
        }

    def __update_article_info(self, article_info_table):
        info_expression_attribute_values = {
            ':article_status': 'public',
            ':one': 1,
            ':topic': self.params['topic'],
            ':tags': TagUtil.get_tags_with_name_collation(self.elasticsearch, self.params.get('tags')),
            ':eye_catch_url': self.params.get('eye_catch_url')
        }

        info_update_expression = 'set #attr = :article_status, sync_elasticsearch = :one, topic = :topic, tags = ' \
                                 ':tags, eye_catch_url=:eye_catch_url'

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression=info_update_expression,
            ExpressionAttributeNames={'#attr': 'status'},
            ExpressionAttributeValues=info_expression_attribute_values
        )

    def __update_paid_article_info(self, article_info_table):
        info_expression_attribute_values = {
            ':article_status': 'public',
            ':one': 1,
            ':topic': self.params['topic'],
            ':tags': TagUtil.get_tags_with_name_collation(self.elasticsearch, self.params.get('tags')),
            ':eye_catch_url': self.params.get('eye_catch_url'),
            ':price': self.params.get('price')
        }

        info_update_expression = 'set #attr = :article_status, sync_elasticsearch = :one, topic = :topic, tags = ' \
                                 ':tags, eye_catch_url=:eye_catch_url, price = :price'

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression=info_update_expression,
            ExpressionAttributeNames={'#attr': 'status'},
            ExpressionAttributeValues=info_expression_attribute_values
        )

    def __delete_article_content_edit(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])
        article_content_edit = article_content_edit_table.get_item(Key={'article_id': self.params['article_id']}).get(
            'Item')

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

        Item = {
            'article_id': article_content['article_id'],
            'title': article_content['title'],
            'body': article_content['body'],
            'created_at': int(time.time())
        }

        # 金額や有料記事本文が含まれている場合一緒に更新する
        if self.params.get('price') is not None and self.params.get('paid_body') is not None:
            Item.update({
                'price': self.params.get('price'),
                'paid_body': self.params.get('paid_body')
            })

        article_history_table.put_item(
            Item=Item
        )

    def __update_paid_body(self, article_content_table):
        article_content_table.update_item(
            Key={
                'article_id': self.params['article_id']
            },
            UpdateExpression="set paid_body=:paid_body",
            ExpressionAttributeValues={
                ':paid_body': self.params.get('paid_body')
            }
        )

    # article_infoからpriceとpaid_bodyを削除する
    def __remove_price_and_paid_body(self, article_info_table, article_content_table):
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
