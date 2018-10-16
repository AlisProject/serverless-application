import os
import json
from unittest import TestCase
from me_external_provider_user_create import MeExternalProviderUserCreate
from unittest.mock import patch
from tests_util import TestsUtil

dynamodb = TestsUtil.get_dynamodb_client()


class TestMeExternalProviderUserCreate(TestCase):

    def setUp(self):
        os.environ['EXTERNAL_PROVIDER_LOGIN_COMMON_TEMP_PASSWORD'] = 'password!'
        os.environ['EXTERNAL_PROVIDER_LOGIN_MARK'] = 'line'
        os.environ['COGNITO_USER_POOL_ID'] = 'xxxxxxx'
        os.environ['COGNITO_USER_POOL_APP_ID'] = 'xxxxxxx'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)

        self.external_provider_users_table_items = [
            {
                'external_provider_user_id': 'LINE_U_test_user',
                'email': 'test01@example.com',
                'password': 'test_pass',
                'iv': 'iv'
            },
            {
                'external_provider_user_id': 'Twitter_test_user',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv',
                'user_id': 'username02'
            },
            {
                'external_provider_user_id': 'Twitter_test_user_2',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv'
            }
        ]
        TestsUtil.create_table(dynamodb, os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'], self.external_provider_users_table_items)

        self.users_table_items = [
            {
                'user_id': 'username02'
            }
        ]
        TestsUtil.create_table(dynamodb, os.environ['USERS_TABLE_NAME'], self.users_table_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(dynamodb)

    def test_main_ok(self):
        with patch('me_external_provider_user_create.UserUtil') as user_mock:
            event = {
                'body': {
                    'user_id': 'username01',
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'LINE_U_test_user',
                        }
                    }
                }
            }

            event['body'] = json.dumps(event['body'])

            user_mock.decrypt_password.return_value = 'password'
            user_mock.create_external_provider_user.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }

            user_mock.wallet_initialization.return_value = None
            user_mock.force_non_verified_phone.return_value = None
            user_mock.add_user_id_to_external_provider_user.return_value = None
            user_mock.delete_external_provider_id_cognito_user.return_value = True
            user_mock.has_user_id.return_value = True
            user_mock.add_user_profile.return_value = None

            response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'username01',
                    'has_user_id': True,
                    'status': 'login'
                }
            )

    def test_already_exist_user_id(self):
        event = {
            'body': {
                'user_id': 'existname',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'Twitter_test_user',
                    }
                }
            }
        }

        event['body'] = json.dumps(event['body'])

        response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_already_added_user_id(self):
        event = {
            'body': {
                'user_id': 'username02',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'LINE_U_test_user',
                    }
                }
            }
        }

        event['body'] = json.dumps(event['body'])

        response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
        self.assertEqual(response['statusCode'], 400)
