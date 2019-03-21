import os
import time

import settings
from time_util import TimeUtil


class NotificationUtil:

    @staticmethod
    def notify_article_comment(dynamodb, article_info, comment, target_user_id, comment_type):
        if comment_type not in settings.COMMENT_NOTIFICATION_TYPES:
            raise ValueError('Invalid comment type ' + comment_type)

        notification_table = dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        notification_id = '-'.join([comment_type, target_user_id, comment['comment_id']])

        notification_table.put_item(Item={
            'notification_id': notification_id,
            'user_id': target_user_id,
            'article_id': article_info['article_id'],
            'article_user_id': article_info['user_id'],
            'article_title': article_info['title'],
            'acted_user_id': comment['user_id'],
            'sort_key': TimeUtil.generate_sort_key(),
            'type': comment_type,
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
