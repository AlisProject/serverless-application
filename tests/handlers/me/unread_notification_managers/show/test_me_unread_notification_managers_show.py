import os
import json
from unittest import TestCase
from me_unread_notification_managers_show import MeUnreadNotificationManagersShow
from tests_util import TestsUtil


class TestMeUnreadNotificationManagersShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        cls.unread_notification_manager_items = [
            {
                'user_id': 'test01',
                'unread': True
            },
            {
                'user_id': 'test02',
                'unread': False
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'],
                               cls.unread_notification_manager_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def test_main_true(self):
        target_data = self.unread_notification_manager_items[0]

        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_data['user_id']
                    }
                }
            }
        }

        me_unread_notification_managers_show = MeUnreadNotificationManagersShow(
            event=params, context={}, dynamodb=self.dynamodb
        )
        response = me_unread_notification_managers_show.main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'unread': True})

    def test_main_false(self):
        target_data = self.unread_notification_manager_items[1]

        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_data['user_id']
                    }
                }
            }
        }

        me_unread_notification_managers_show = MeUnreadNotificationManagersShow(
            event=params, context={}, dynamodb=self.dynamodb
        )
        response = me_unread_notification_managers_show.main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'unread': False})

    def test_main_false_with_no_resource(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03'
                    }
                }
            }
        }

        me_unread_notification_managers_show = MeUnreadNotificationManagersShow(
            event=params, context={}, dynamodb=self.dynamodb
        )
        response = me_unread_notification_managers_show.main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'unread': False})
