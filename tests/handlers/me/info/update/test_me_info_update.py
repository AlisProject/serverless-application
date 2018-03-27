import os
import boto3
import json
import settings
from unittest import TestCase
from me_info_update import MeInfoUpdate
from unittest.mock import patch, MagicMock
from boto3.dynamodb.conditions import Key
from tests_util import TestsUtil


class TestMeInfosUpdate(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create users_table
        cls.users_table_items = [
            {
                'user_id': 'test01'
            },
            {
                'user_id': 'test02',
                'user_display_name': 'test_display_name02',
                'self_introduction': 'test_introduction02'
            },
            {
                'user_id': 'test03',
                'user_display_name': 'test_display_name03',
                'self_introduction': 'test_introduction03'
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['USERS_TABLE_NAME'], cls.users_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        test_function = MeInfoUpdate(event=params, context={}, dynamodb=self.dynamodb)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        target_user_data = self.users_table_items[0]

        params = {
            'body': {
                'user_display_name': 'display_name_01',
                'self_introduction': 'self_introduction_01'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user_data['user_id']
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        me_infos_update = MeInfoUpdate(event=params, context={}, dynamodb=self.dynamodb)
        response = me_infos_update.main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': target_user_data['user_id']}).get('Item')

        expected_items = {
            'user_id': target_user_data['user_id'],
            'user_display_name': json.loads(params['body'])['user_display_name'],
            'self_introduction': json.loads(params['body'])['self_introduction']
        }

        self.assertEqual(response['statusCode'], 200)
        users_param_names = ['user_id', 'user_display_name', 'self_introduction']
        for key in users_param_names:
            self.assertEqual(expected_items[key], user[key])

    def test_main_ok_exists_infos(self):
        target_user_data = self.users_table_items[1]

        params = {
            'body': {
                'user_display_name': 'display_name_02',
                'self_introduction': 'self_introduction_02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user_data['user_id']
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        me_infos_update = MeInfoUpdate(event=params, context={}, dynamodb=self.dynamodb)
        response = me_infos_update.main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': target_user_data['user_id']}).get('Item')

        expected_items = {
            'user_id': target_user_data['user_id'],
            'user_display_name': json.loads(params['body'])['user_display_name'],
            'self_introduction': json.loads(params['body'])['self_introduction']
        }

        self.assertEqual(response['statusCode'], 200)
        users_param_names = ['user_id', 'user_display_name', 'self_introduction']
        for key in users_param_names:
            self.assertEqual(expected_items[key], user[key])

    def test_main_ok_with_maxLength(self):
        target_user_data = self.users_table_items[2]

        params = {
            'body': {
                'user_display_name': '亜' * settings.parameters['user_display_name']['maxLength'],
                'self_introduction': '伊' * settings.parameters['self_introduction']['maxLength']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user_data['user_id']
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        me_infos_update = MeInfoUpdate(event=params, context={}, dynamodb=self.dynamodb)
        response = me_infos_update.main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': target_user_data['user_id']}).get('Item')

        expected_items = {
            'user_id': target_user_data['user_id'],
            'user_display_name': json.loads(params['body'])['user_display_name'],
            'self_introduction': json.loads(params['body'])['self_introduction']
        }

        self.assertEqual(response['statusCode'], 200)
        users_param_names = ['user_id', 'user_display_name', 'self_introduction']
        for key in users_param_names:
            self.assertEqual(expected_items[key], user[key])

    def test_main_ok_with_minLength_and_empty(self):
        target_user_data = self.users_table_items[2]

        params = {
            'body': {
                'user_display_name': '亜' * settings.parameters['user_display_name']['minLength'],
                'self_introduction': ''
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user_data['user_id']
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        me_infos_update = MeInfoUpdate(event=params, context={}, dynamodb=self.dynamodb)
        response = me_infos_update.main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': target_user_data['user_id']}).get('Item')

        expected_items = {
            'user_id': target_user_data['user_id'],
            'user_display_name': json.loads(params['body'])['user_display_name'],
            'self_introduction': None
        }

        self.assertEqual(response['statusCode'], 200)
        users_param_names = ['user_id', 'user_display_name', 'self_introduction']
        for key in users_param_names:
            self.assertEqual(expected_items[key], user[key])

    def test_main_ok_with_script_tag(self):
        target_user_data = self.users_table_items[2]

        params = {
            'body': {
                'user_display_name': "a<script>alert('ab')</script>b",
                'self_introduction': "c<script>alert('cd')</script>d"
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user_data['user_id']
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        me_infos_update = MeInfoUpdate(event=params, context={}, dynamodb=self.dynamodb)
        response = me_infos_update.main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': target_user_data['user_id']}).get('Item')

        expected_items = {
            'user_id': target_user_data['user_id'],
            'user_display_name': "a&lt;script&gt;alert('ab')&lt;/script&gt;b",
            'self_introduction': "c&lt;script&gt;alert('cd')&lt;/script&gt;d"
        }

        self.assertEqual(response['statusCode'], 200)
        users_param_names = ['user_id', 'user_display_name', 'self_introduction']
        for key in users_param_names:
            self.assertEqual(expected_items[key], user[key])

    def test_call_validate_user_existence(self):
        target_user_data = self.users_table_items[2]

        params = {
            'body': {
                'user_display_name': 'display_name_03',
                'self_introduction': 'self_introduction_03'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user_data['user_id']
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_info_update.DBUtil', mock_lib):
            MeInfoUpdate(event=params, context={}, dynamodb=self.dynamodb).main()
            args, kwargs = mock_lib.validate_user_existence.call_args

            self.assertTrue(mock_lib.validate_user_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_display_name_max(self):
        params = {
            'queryStringParameters': {
                'user_display_name': 'A' * (settings.parameters['user_display_name']['maxLength'] + 1),
                'self_introduction': 'test'
            }
        }

        self.assert_bad_request(params)

    def test_validation_display_name_min(self):
        params = {
            'queryStringParameters': {
                'user_display_name': 'A' * (settings.parameters['user_display_name']['minLength'] - 1),
                'self_introduction': 'test'
            }
        }

        self.assert_bad_request(params)

    def test_validation_self_introduction_max(self):
        params = {
            'queryStringParameters': {
                'user_display_name': 'test',
                'self_introduction': 'A' * (settings.parameters['self_introduction']['maxLength'] + 1),
            }
        }

        self.assert_bad_request(params)
