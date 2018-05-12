import os
import json
from unittest import TestCase
from me_notifications_index import MeNotificationsIndex
from tests_util import TestsUtil


class TestMeUnreadNotificationManagersShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        cls.notification_items = [
            {
                'user_id': 'test01',
                'sort_key': 1520150272000000,
                'type': 'like',
                'acted_user_id': 'acted_user01',
                'created_at': 1520150272
            },
            {
                'user_id': 'test01',
                'sort_key': 1520150272000001,
                'type': 'like',
                'acted_user_id': 'acted_user02',
                'created_at': 1520150272
            },
            {
                'user_id': 'test01',
                'sort_key': 1520150272000002,
                'type': 'like',
                'acted_user_id': 'acted_user03',
                'created_at': 1520150272
            },
            {
                'user_id': 'test02',
                'sort_key': 1520150272000000,
                'type': 'like',
                'acted_user_id': 'acted_user01',
                'created_at': 1520150272
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['NOTIFICATION_TABLE_NAME'],cls.notification_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = MeNotificationsIndex(event=params, context={}, dynamodb=self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '2'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        me_notifications_index = MeNotificationsIndex(event=params, context={}, dynamodb=self.dynamodb)
        response = me_notifications_index.main()

        expected_items = [
            {
                'user_id': 'test01',
                'sort_key': 1520150272000002,
                'type': 'like',
                'acted_user_id': 'acted_user03',
                'created_at': 1520150272
            },
            {
                'user_id': 'test01',
                'sort_key': 1520150272000001,
                'type': 'like',
                'acted_user_id': 'acted_user02',
                'created_at': 1520150272
            }
        ]

        expected_evaluated_key = {
            'user_id': 'test01',
            'sort_key': 1520150272000001
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)
        self.assertEqual(json.loads(response['body'])['LastEvaluatedKey'], expected_evaluated_key)

    def test_main_ok_with_evaluated_key(self):
        params = {
            'queryStringParameters': {
                'limit': '2',
                'sort_key': '1520150272000001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        me_notifications_index = MeNotificationsIndex(event=params, context={}, dynamodb=self.dynamodb)
        response = me_notifications_index.main()

        expected_items = [
            {
                'user_id': 'test01',
                'sort_key': 1520150272000000,
                'type': 'like',
                'acted_user_id': 'acted_user01',
                'created_at': 1520150272
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_no_limit(self):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        for i in range(11):
            notification_table.put_item(Item={
                    'user_id': 'nolimit01',
                    'sort_key': 1520150273000000 + i,
                    'type': 'like',
                    'acted_user_id': 'acted_user' + str(i),
                    'created_at': 1520150273
                }
            )

        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'nolimit01'
                    }
                }
            }
        }

        me_notifications_index = MeNotificationsIndex(event=params, context={}, dynamodb=self.dynamodb)
        response = me_notifications_index.main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_validation_with_no_query_params(self):
        params = {
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        response = MeNotificationsIndex(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

    def test_validation_limit_type(self):
        params = {
            'queryStringParameters': {
                'limit': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_max(self):
        params = {
            'queryStringParameters': {
                'limit': '101'
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_min(self):
        params = {
            'queryStringParameters': {
                'limit': '0'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_type(self):
        params = {
            'queryStringParameters': {
                'sort_key': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_max(self):
        params = {
            'queryStringParameters': {
                'sort_key': '2147483647000001'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_min(self):
        params = {
            'queryStringParameters': {
                'sort_key': '0'
            }
        }

        self.assert_bad_request(params)
