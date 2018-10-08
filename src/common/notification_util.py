import os
import time

import settings
from time_util import TimeUtil


class NotificationUtil:
    @staticmethod
    def notify_comment_mention(dynamodb, article_info, mentioned_user_id, acted_user_id, comment_id):
        notification_table = dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        notification_id = '-'.join(
            [settings.COMMENT_MENTION_NOTIFICATION_TYPE, mentioned_user_id, comment_id])

        notification_table.put_item(Item={
            'notification_id': notification_id,
            'user_id': mentioned_user_id,
            'article_id': article_info['article_id'],
            'article_title': article_info['title'],
            'acted_user_id': acted_user_id,
            'sort_key': TimeUtil.generate_sort_key(),
            'type': settings.COMMENT_MENTION_NOTIFICATION_TYPE,
            'created_at': int(time.time())
        })

    @staticmethod
    def notify_comment(dynamodb, article_info, user_id, comment_id):
        notification_table = dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        notification_id = '-'.join(
            [settings.COMMENT_NOTIFICATION_TYPE, article_info['user_id'], comment_id])

        notification_table.put_item(Item={
            'notification_id': notification_id,
            'user_id': article_info['user_id'],
            'article_id': article_info['article_id'],
            'article_title': article_info['title'],
            'acted_user_id': user_id,
            'sort_key': TimeUtil.generate_sort_key(),
            'type': settings.COMMENT_NOTIFICATION_TYPE,
            'created_at': int(time.time())
        })

    @staticmethod
    def update_unread_notification_manager(dynamodb, user_id):
        unread_notification_manager_table = dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        unread_notification_manager_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )
