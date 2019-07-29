import json
import os
import settings
from unittest import TestCase
from tests_util import TestsUtil
from me_configurations_mute_users_add import MeConfigurationsMuteUsersAdd


class TestMeConfigurationsMuteUsersAdd(TestCase):
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
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USERS_TABLE_NAME'], self.users_table_items)

        # create user_configurations_table
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'], [])

        # backup settings
        self.tmp_mute_users_max_count = settings.MUTE_USERS_MAX_COUNT

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)
        # restore settings
        settings.MUTE_USERS_MAX_COUNT = self.tmp_mute_users_max_count

    def assert_bad_request(self, params):
        response = MeConfigurationsMuteUsersAdd(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        test_user = 'test-user-00'

        # 初回登録
        params = {
            'body': {
                'mute_user_id': self.users_table_items[0]['user_id']
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                self.users_table_items[0]['user_id']
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

        # 追加
        params = {
            'body': {
                'mute_user_id': self.users_table_items[1]['user_id']
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                self.users_table_items[0]['user_id'],
                self.users_table_items[1]['user_id']
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

    def test_main_ok_with_same_user(self):
        test_user = 'test-user-00'

        # 初回登録
        params = {
            'body': {
                'mute_user_id': self.users_table_items[0]['user_id']
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                self.users_table_items[0]['user_id']
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

        # 同一ユーザで登録しても正常終了すること
        params = {
            'body': {
                'mute_user_id': self.users_table_items[0]['user_id']
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                self.users_table_items[0]['user_id']
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

    def test_main_ok_not_exists_mute_users(self):
        # mute_users が存在しないデータを作成
        test_user = 'test-user-00'
        params = {
            'user_id': test_user
        }
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        user_configurations_table.put_item(Item=params)

        # mute_users が存在しない状態で追加
        params = {
            'body': {
                'mute_user_id': self.users_table_items[0]['user_id']
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                self.users_table_items[0]['user_id']
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

    def test_main_ng_with_limit_exceeded(self):
        settings.MUTE_USERS_MAX_COUNT = 1
        test_user = 'test-user-00'

        # 初回登録
        params = {
            'body': {
                'mute_user_id': self.users_table_items[0]['user_id']
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {
                self.users_table_items[0]['user_id']
            }
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

        # 追加
        params = {
            'body': {
                'mute_user_id': self.users_table_items[1]['user_id']
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        # データが変更されていないこと
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        # status 400 で返却されること
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '{"message": "Limit exceeded: mute users"}')

    def test_main_ng_specified_not_exists_user(self):
        test_user = 'test-user-00'

        params = {
            'body': {
                'mute_user_id': 'test-user-01'
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
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(response['body'], '{"message": "Record Not Found"}')

    def test_main_ng_specified_own_user(self):
        params = {
            'body': {
                'mute_user_id': self.users_table_items[0]['user_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.users_table_items[0]['user_id']
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])
        response = MeConfigurationsMuteUsersAdd(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '{"message": "Invalid parameter: mute-user-00 is own user."}')

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
