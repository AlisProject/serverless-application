import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from tests_util import TestsUtil

import settings
from notification_util import NotificationUtil


class TestNotificationUtil(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['NOTIFICATION_TABLE_NAME'], [])

        self.unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        self.unread_notification_manager_items = [
            {
                'user_id': 'user_id_00',
                'unread': False
            }
        ]
        TestsUtil.create_table(
            self.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'],
            self.unread_notification_manager_items
        )

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def notify_article_comment_with_invalid_type(self):
        comment = {
            'comment_id': 'comment_id',
            'user_id': 'comment_user01'
        }

        article_info = {
            'article_id': 'ARTICLEID01',
            'user_id': 'article_user01',
            'title': 'AAAAAAAAAAAAAAAA'
        }

        target_user_id = 'target_user_id'

        with self.assertRaises(ValueError):
            NotificationUtil.notify_article_comment(self.dynamodb, article_info, comment, target_user_id, 'ALIS')

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def notify_article_comment(self):
        comment = {
            'comment_id': 'comment_id',
            'user_id': 'comment_user01'
        }

        article_info = {
            'article_id': 'ARTICLEID01',
            'user_id': 'article_user01',
            'title': 'AAAAAAAAAAAAAAAA'
        }

        target_user_id = 'target_user_id'

        for comment_type in settings.COMMENT_NOTIFICATION_TYPES:
            NotificationUtil.notify_article_comment(self.dynamodb, article_info, comment, target_user_id, comment_type)

            notification_id = '-'.join([comment_type, target_user_id, comment['comment_id']])

            notification = self.notification_table.get_item(
                Key={'notification_id': notification_id}
            ).get('Item')

            expected_notification = {
                'notification_id': notification_id,
                'user_id': target_user_id,
                'article_id': article_info['article_id'],
                'article_title': article_info['title'],
                'acted_user_id': comment['user_id'],
                'sort_key': 1520150552000003,
                'type': comment_type,
                'created_at': 1520150552
            }

            self.assertEqual(notification, expected_notification)

    def test_update_unread_notification_manager(self):

        before = self.unread_notification_manager_table.scan()['Items']
        NotificationUtil.update_unread_notification_manager(
            self.dynamodb,
            self.unread_notification_manager_items[0]['user_id']
        )
        NotificationUtil.update_unread_notification_manager(self.dynamodb, 'new_user')
        after = self.unread_notification_manager_table.scan()['Items']

        self.assertEqual(len(after) - len(before), 1)

        expected_unread_manager = [
            {
                'user_id': self.unread_notification_manager_items[0]['user_id'],
                'unread': True
            },
            {
                'user_id': 'new_user',
                'unread': True
            }
        ]

        self.assertEqual(after, expected_unread_manager)
