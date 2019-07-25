import json
import os
from unittest import TestCase
from tests_util import TestsUtil
from me_configures_mute_users_delete import MeConfiguresMuteUsersDelete


class TestMeConfiguresMuteUsersDelete(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        # create users_table
        self.users_table_items = [
            {
                'user_id': 'mute-user-00'
            },
            {
                'user_id': 'mute-user-01'
            },
            {
                'user_id': 'mute-user-02'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USERS_TABLE_NAME'], self.users_table_items)

        # create user_configurations_table
        self.user_configurations_items = [
            {
                'user_id': 'test-user-00',
                'mute_users': {'mute-user-00', 'mute-user-01'}
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'],
                               self.user_configurations_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        response = MeConfiguresMuteUsersDelete(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        test_user = 'test-user-00'

        # 1件目削除
        params = {
            'body': {
                'mute_user_id': 'mute-user-00'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])
        response = MeConfiguresMuteUsersDelete(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                'mute-user-01'
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

        # 2件目削除（全 mute-user を削除）
        params = {
            'body': {
                'mute_user_id': 'mute-user-01'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])
        response = MeConfiguresMuteUsersDelete(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

        # mute_users が登録されていない状態で削除処理が流れても例外が発生しないこと
        params = {
            'body': {
                'mute_user_id': 'mute-user-02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])
        response = MeConfiguresMuteUsersDelete(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

    def test_main_ok_specified_not_exists_mute_user(self):
        test_user = 'test-user-00'

        # 存在しない mute_user を指定しても例外が発生しないこと
        params = {
            'body': {
                'mute_user_id': 'mute-user-02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])
        response = MeConfiguresMuteUsersDelete(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                'mute-user-00',
                'mute-user-01'
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

    def test_validation_mute_user_id_required(self):
        params = {
            'pathParameters': {}
        }
        self.assert_bad_request(params)

    def test_validation_mute_user_id_min(self):
        params = {
            'pathParameters': {
                'mute_user_id': 'A' * 2
            }
        }
        self.assert_bad_request(params)

    def test_validation_mute_user_id_max(self):
        params = {
            'pathParameters': {
                'mute_user_id': 'A' * 51
            }
        }
        self.assert_bad_request(params)
