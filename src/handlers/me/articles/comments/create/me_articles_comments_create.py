# -*- coding: utf-8 -*-
import json
import logging
import os
import traceback

import settings
import time

from db_util import DBUtil
from hashids import Hashids
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil
from text_sanitizer import TextSanitizer


class MeArticlesCommentsCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'text': settings.parameters['comment']['text']
            },
            'required': ['article_id', 'text']
        }

    def validate_params(self):
        if not self.event.get('body'):
            raise ValidationError('Request parameter is required')

        validate(self.params, self.get_schema())
        DBUtil.validate_article_existence(self.dynamodb, self.params['article_id'], status='public')

    def exec_main_proc(self):
        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        comment_id = self.__generate_comment_id(sort_key)

        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': user_id}).get('Item')
        comment = {
            'comment_id': comment_id,
            'article_id': self.params['article_id'],
            'text': TextSanitizer.sanitize_text(self.params['text']),
            'user_id': user_id,
            'sort_key': sort_key,
            'created_at': int(time.time())
        }
        if 'alias_user_id' in user:
            comment.update({'alias_user_id': user['alias_user_id']})

        comment_table.put_item(
            Item=comment,
            ConditionExpression='attribute_not_exists(comment_id)'
        )

        # 優先度が低いため通知処理は失敗しても握り潰して200を返す（ログは出して検知できるようにする）
        try:
            article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
            article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']})['Item']

            if self.__is_notifiable_comment(article_info, user_id):
                self.__create_comment_notification(article_info, comment_id, user_id, user)
                self.__update_unread_notification_manager(article_info)

        except Exception as err:
            logging.fatal(err)
            traceback.print_exc()
        finally:
            return {
                'statusCode': 200,
                'body': json.dumps({'comment_id': comment_id})
            }

    def __is_notifiable_comment(self, article_info, user_id):
        return False if article_info['user_id'] == user_id else True

    def __create_comment_notification(self, article_info, comment_id, user_id, user):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        notification_id = '-'.join(
            [settings.COMMENT_NOTIFICATION_TYPE, article_info['user_id'], comment_id])
        has_alias_user_id_article = True if 'alias_user_id' in article_info else False
        has_alias_user_id = True if 'alias_user_id' in user else False
        Item = {
            'notification_id': notification_id,
            'user_id': article_info['user_id'],
            'article_id': article_info['article_id'],
            'article_title': article_info['title'],
            'acted_user_id': user_id,
            'sort_key': TimeUtil.generate_sort_key(),
            'type': settings.COMMENT_NOTIFICATION_TYPE,
            'created_at': int(time.time())
        }
        if has_alias_user_id_article:
            Item.update({'alias_user_id': article_info['alias_user_id']})
        if has_alias_user_id:
            Item.update({'acted_alias_user_id': user['alias_user_id']})

        notification_table.put_item(Item=Item)

    def __update_unread_notification_manager(self, article_info):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        unread_notification_manager_table.update_item(
            Key={'user_id': article_info['user_id']},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )

    def __generate_comment_id(self, target):
        hashids = Hashids(salt=os.environ['SALT_FOR_ARTICLE_ID'], min_length=settings.COMMENT_ID_LENGTH)
        return hashids.encode(target)
