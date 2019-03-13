# -*- coding: utf-8 -*-
import os
import json
import logging
import traceback
import settings
import time
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from hashids import Hashids
from time_util import TimeUtil
from db_util import DBUtil
from user_util import UserUtil


class MeArticlesDraftsArticleIdCreate(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

    def exec_main_proc(self):
        sort_key = TimeUtil.generate_sort_key()
        article_id = self.__generate_article_id(sort_key)

        try:
            self.__create_article_info(sort_key, article_id)

            try:
                self.__create_article_content(article_id)
            except Exception as err:
                logging.fatal(err)
                traceback.print_exc()
            finally:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'article_id': article_id})
                }
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'Already exists'})
                }
            else:
                raise

    def __create_article_info(self, sort_key, article_id):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info = {
            'article_id': article_id,
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'status': 'draft',
            'sort_key': sort_key,
            'created_at': int(time.time()),
            'version': 2
        }
        DBUtil.items_values_empty_to_none(article_info)

        article_info_table.put_item(
            Item=article_info,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __create_article_content(self, article_id):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_content = {
            'article_id': article_id,
            'created_at': int(time.time())
        }
        DBUtil.items_values_empty_to_none(article_content)

        article_content_table.put_item(
            Item=article_content,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __generate_article_id(self, target):
        hashids = Hashids(salt=os.environ['SALT_FOR_ARTICLE_ID'], min_length=settings.article_id_length)
        return hashids.encode(target)
