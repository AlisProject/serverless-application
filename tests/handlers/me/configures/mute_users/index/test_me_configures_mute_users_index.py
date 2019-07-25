import json
import os
from unittest import TestCase
from tests_util import TestsUtil
from me_configures_mute_users_index import MeConfiguresMuteUsersIndex


class TestMeConfiguresMuteUsersIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        # create user_configurations_table
        self.user_configurations_items = [
            {
                'user_id': 'test-user-00',
                'mute_users': {'mute-user-02', 'mute-user-00', 'mute-user-00'}
            },
            {
                'user_id': 'test-user-01'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'],
                               self.user_configurations_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        response = MeConfiguresMuteUsersIndex(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.user_configurations_items[0]['user_id']
                    }
                }
            }
        }
        response = MeConfiguresMuteUsersIndex(event=params, context={}, dynamodb=self.dynamodb).main()
        mute_users = list(self.user_configurations_items[0]['mute_users'])
        # ユーザID の昇順でソートされていること
        mute_users.sort()
        expected = {
            'mute_users': mute_users
        }
        self.assertEqual(expected, json.loads(response['body']))
        self.assertEqual(response['statusCode'], 200)

    def test_main_ok_not_exists_mute_users(self):
        # mute_users が登録されていないユーザの場合、空の配列が返却されること
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.user_configurations_items[1]['user_id']
                    }
                }
            }
        }
        response = MeConfiguresMuteUsersIndex(event=params, context={}, dynamodb=self.dynamodb).main()
        expected = {
            'mute_users': []
        }
        self.assertEqual(expected, json.loads(response['body']))
        self.assertEqual(response['statusCode'], 200)

    def test_main_ok_not_exists_from_user_configurations(self):
        # user_configurations テーブルに登録されていないユーザの場合、空の配列が返却されること
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'hoge-user_00'
                    }
                }
            }
        }
        response = MeConfiguresMuteUsersIndex(event=params, context={}, dynamodb=self.dynamodb).main()
        expected = {
            'mute_users': []
        }
        self.assertEqual(expected, json.loads(response['body']))
        self.assertEqual(response['statusCode'], 200)
