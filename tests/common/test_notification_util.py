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

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_notify_comment_mention(self):
        article_info = {
            'article_id': 'testid000001',
            'user_id': 'matsumatsu20',
            'created_at': 1520150272,
            'title': 'title02',
            'overview': 'overview01',
            'status': 'public',
            'topic': 'crypto',
            'article_score': 12,
            'sort_key': 1520150272000001
        }
        mentioned_id = 'mentioned_id01'
        acted_user_id = 'acted_user_id01'
        comment_id = 'HOGEHOGEHOGE'

        notification_before = self.notification_table.scan()['Items']
        NotificationUtil.notify_comment_mention(self.dynamodb, article_info, mentioned_id, acted_user_id, comment_id)
        notification_after = self.notification_table.scan()['Items']

        self.assertEqual(len(notification_after) - len(notification_before), 1)

        expected_notification = {
            'notification_id': 'comment_mention-mentioned_id01-HOGEHOGEHOGE',
            'user_id': mentioned_id,
            'article_id': article_info['article_id'],
            'article_title': article_info['title'],
            'acted_user_id': acted_user_id,
            'sort_key': 1520150552000003,
            'type': settings.COMMENT_MENTION_NOTIFICATION_TYPE,
            'created_at': 1520150552
        }

        for key, value in notification_after[0].items():
            self.assertEqual(value, expected_notification[key])

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_notify_comment(self):
        article_info = {
            'article_id': 'testid000002',
            'user_id': 'matsumatsu20',
            'created_at': 1520150272,
            'title': 'title02',
            'overview': 'overview02',
            'status': 'public',
            'topic': 'crypto',
            'article_score': 12,
            'sort_key': 1520150272000001
        }
        acted_user_id = 'acted_user_id02'
        comment_id = 'FUGAFUGAFUGA'

        notification_before = self.notification_table.scan()['Items']
        NotificationUtil.notify_comment(self.dynamodb, article_info, acted_user_id, comment_id)
        notification_after = self.notification_table.scan()['Items']

        self.assertEqual(len(notification_after) - len(notification_before), 1)

        expected_notification = {
            'notification_id': 'comment-matsumatsu20-FUGAFUGAFUGA',
            'user_id': article_info['user_id'],
            'article_id': article_info['article_id'],
            'article_title': article_info['title'],
            'acted_user_id': acted_user_id,
            'sort_key': 1520150552000003,
            'type': settings.COMMENT_NOTIFICATION_TYPE,
            'created_at': 1520150552
        }

        self.assertEqual(notification_after[0], expected_notification)

    def test_update_unread_notification_manager(self):

        before = self.unread_notification_manager_table.scan()['Items']
        print(before)
        NotificationUtil.update_unread_notification_manager(
            self.dynamodb,
            self.unread_notification_manager_items[0]['user_id']
        )
        NotificationUtil.update_unread_notification_manager(self.dynamodb, 'new_user')
        after = self.unread_notification_manager_table.scan()['Items']

        # print(after)

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





