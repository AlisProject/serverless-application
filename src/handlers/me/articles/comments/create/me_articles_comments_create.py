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

from notification_util import NotificationUtil
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
        comment_body = TextSanitizer.sanitize_text(self.params['text'])

        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])

        comment = {
            'comment_id': comment_id,
            'article_id': self.params['article_id'],
            'text': comment_body,
            'user_id': user_id,
            'sort_key': sort_key,
            'created_at': int(time.time())
        }

        comment_table.put_item(
            Item=comment,
            ConditionExpression='attribute_not_exists(comment_id)'
        )

        # 優先度が低いため通知処理は失敗しても握り潰して200を返す（ログは出して検知できるようにする）
        try:
            article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
            article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']})['Item']

            self.__create_comment_notifications(article_info, comment_body, comment_id, user_id)

        except Exception as err:
            logging.fatal(err)
            traceback.print_exc()
        finally:
            return {
                'statusCode': 200,
                'body': json.dumps({'comment_id': comment_id})
            }

    def __create_comment_notifications(self, article_info, comment_body, comment_id, user_id):
        mentioned_user_ids = self.__get_user_ids_from_comment_body(comment_body)

        # コメントでメンションされたユーザへの通知処理
        for mentioned_user_id in mentioned_user_ids:
            NotificationUtil.notify_comment_mention(self.dynamodb, article_info, mentioned_user_id, user_id, comment_id)
            NotificationUtil.update_unread_notification_manager(self.dynamodb, mentioned_user_id)

        # メンション通知対象に記事投稿者入っている場合、または記事投稿者自身によるコメントの場合は通常のコメント通知をSKIPする。
        if not article_info['user_id'] in mentioned_user_ids and not article_info['user_id'] == user_id:
            NotificationUtil.notify_comment(self.dynamodb, article_info, user_id, comment_id)
            NotificationUtil.update_unread_notification_manager(self.dynamodb, article_info['user_id'])

    def __update_unread_notification_manager(self, user_id):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        unread_notification_manager_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )

    def __generate_comment_id(self, target):
        hashids = Hashids(salt=os.environ['SALT_FOR_ARTICLE_ID'], min_length=settings.COMMENT_ID_LENGTH)
        return hashids.encode(target)

    def __get_user_ids_from_comment_body(self, comment_body):
        user_ids = []

        for words in comment_body.split():
            if not words.startswith('@'):
                continue

            mentioned_user_id = words[1:]

            # 実際にDBに存在するユーザIDでない場合は集計対象としない
            if DBUtil.exists_user(self.dynamodb, mentioned_user_id):
                user_ids.append(mentioned_user_id)

        return user_ids
