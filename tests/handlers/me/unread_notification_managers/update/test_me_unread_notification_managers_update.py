import os
from unittest import TestCase
from me_unread_notification_managers_update import MeUnreadNotificationManagersUpdate
from tests_util import TestsUtil


class TestMeUnreadNotificationManagersUpdate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        cls.unread_notification_manager_items = [
            {
                'user_id': 'test01',
                'unread': False
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'],
                               cls.unread_notification_manager_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def test_main_ok(self):
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

        me_unread_notification_managers_update = MeUnreadNotificationManagersUpdate(
            event=params, context={}, dynamodb=self.dynamodb
        )
        response = me_unread_notification_managers_update.main()

        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        target = unread_notification_manager_table.get_item(Key={'user_id': target_data['user_id']}).get('Item')

        expected_items = {
            'user_id': target_data['user_id'],
            'unread': True
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(expected_items, target)

    def test_main_ok_with_no_resource(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test2'
                    }
                }
            }
        }

        me_unread_notification_managers_update = MeUnreadNotificationManagersUpdate(
            event=params, context={}, dynamodb=self.dynamodb
        )
        response = me_unread_notification_managers_update.main()

        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        target = unread_notification_manager_table.get_item(Key={'user_id': 'test2'}).get('Item')

        expected_items = {
            'user_id': 'test2',
            'unread': True
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(expected_items, target)
