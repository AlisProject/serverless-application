# -*- coding: utf-8 -*-
import json
import logging
import os
import traceback

from boto3.dynamodb.conditions import Key

import settings
import time

from db_util import DBUtil
from hashids import Hashids
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError

from notification_util import NotificationUtil
from time_util import TimeUtil
from text_sanitizer import TextSanitizer
from user_util import UserUtil


class MeArticlesCommentsReply(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'text': settings.parameters['comment']['text'],
                'parent_id': settings.parameters['comment']['comment_id'],
                'reply_user_id': settings.parameters['user_id']
            },
            'required': ['article_id', 'text', 'parent_id', 'reply_user_id']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        if not self.event.get('body'):
            raise ValidationError('Request parameter is required')

        validate(self.params, self.get_schema())
        DBUtil.validate_article_existence(self.dynamodb, self.params['article_id'], status='public')
        DBUtil.validate_parent_comment_existence(self.dynamodb, self.params['parent_id'])
        DBUtil.validate_user_existence(self.dynamodb, self.params['reply_user_id'])

    def exec_main_proc(self):
        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        comment_id = self.__generate_comment_id(sort_key)

        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])

        comment = {
            'comment_id': comment_id,
            'article_id': self.params['article_id'],
            'text': TextSanitizer.sanitize_text(self.params['text']),
            'parent_id': self.params['parent_id'],
            'reply_user_id': self.params['reply_user_id'],
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

            self.__create_comment_notifications(article_info, comment)

        except Exception as err:
            logging.fatal(err)
            traceback.print_exc()
        finally:
            return {
                'statusCode': 200,
                'body': json.dumps({'comment_id': comment_id})
            }

    def __create_comment_notifications(self, article_info, comment):
        notification_tagets = []

        # 返信先のユーザーへの通知(自分自身に返信も可能なため、その場合は通知しない)
        if not self.params['reply_user_id'] == comment['user_id']:
            NotificationUtil.notify_article_comment(
                self.dynamodb, article_info, comment, self.params['reply_user_id'], settings.COMMENT_REPLY_NOTIFICATION_TYPE
            )
            notification_tagets.append(self.params['reply_user_id'])

        # スレッド内のユーザへの通知
        thread_notification_targets = self.__get_thread_notification_targets(
            comment['user_id'], self.params['reply_user_id'], self.params['parent_id'])
        notification_tagets.extend(thread_notification_targets)
        for target_user_id in thread_notification_targets:
            NotificationUtil.notify_article_comment(
                self.dynamodb, article_info, comment, target_user_id, settings.COMMENT_THREAD_NOTIFICATION_TYPE
            )

        # 記事作成者が上記の通知処理の対象に含まれていない、かつコメントの登録者ではない場合は記事作成者に通知する
        if not article_info['user_id'] in notification_tagets and not article_info['user_id'] == comment['user_id']:
            NotificationUtil.notify_article_comment(
                self.dynamodb, article_info, comment, article_info['user_id'], settings.COMMENT_NOTIFICATION_TYPE
            )
            notification_tagets.append(article_info['user_id'])

        # 通知ユーザは通知未読扱いに更新する
        for target_user_id in notification_tagets:
            NotificationUtil.update_unread_notification_manager(self.dynamodb, target_user_id)

    def __get_thread_notification_targets(self, user_id, reply_user_id, parent_id):
        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])

        query_params = {
            'IndexName': 'parent_id-sort_key-index',
            'KeyConditionExpression': Key('parent_id').eq(parent_id)
        }

        thread_comments = comment_table.query(**query_params)['Items']
        thread_user_ids = [comment['user_id'] for comment in thread_comments]
        parent_comment = comment_table.get_item(Key={'comment_id': parent_id})['Item']

        # スレッドコメントのユーザーと親コメントのユーザーが通知対象になる
        target_user_ids = list(set(thread_user_ids + [parent_comment['user_id']]))

        # 通知対象から返信先のユーザーと返信したユーザーを削除する。存在しない場合は無視して後続処理を続ける
        for user_id in [user_id, reply_user_id]:
            try:
                target_user_ids.remove(user_id)
            except ValueError:
                pass

        return target_user_ids

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
