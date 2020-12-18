import os
import json
from unittest import TestCase
from me_external_provider_user_create import MeExternalProviderUserCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from record_not_found_error import RecordNotFoundError

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
                'external_provider_user_id': 'LINE-U-test-user',
                'email': 'test01@example.com',
                'password': 'test_pass',
                'iv': 'iv'
            },
            {
                'external_provider_user_id': 'Twitter-test-user',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv',
                'user_id': 'username02'
            },
            {
                'external_provider_user_id': 'Twitter-test-user-2',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv'
            }
        ]
        TestsUtil.create_table(
          dynamodb,
          os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'],
          self.external_provider_users_table_items
        )

        self.users_table_items = [
            {
                'user_id': 'username02'
            }
        ]
        TestsUtil.create_table(dynamodb, os.environ['USERS_TABLE_NAME'], self.users_table_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(dynamodb)

    @patch('me_external_provider_user_create.UserUtil.delete_external_provider_id_cognito_user',
           MagicMock(return_value=True))
    @patch('me_external_provider_user_create.UserUtil.force_non_verified_phone', MagicMock(return_value=None))
    @patch('me_external_provider_user_create.CryptoUtil', MagicMock(return_value='password'))
    def test_main_ok(self):
        with patch('me_external_provider_user_create.UserUtil.create_external_provider_user') as create_external_mock, \
             patch('me_external_provider_user_create.UserUtil.get_cognito_user_info') as get_cognito_user_mock:
            create_external_mock.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            get_cognito_user_mock.side_effect = RecordNotFoundError('Record Not Found')

            event = {
                'body': {
                    'user_id': 'username01',
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'LINE-U-test-user',
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

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
        with patch('me_external_provider_user_create.UserUtil') as user_mock:
            event = {
                'body': {
                    'user_id': 'existname',
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'Twitter-test-user',
                        }
                    }
                }
            }

            event['body'] = json.dumps(event['body'])

            user_mock.get_cognito_user_info.side_effect = RecordNotFoundError('Record Not Found')

            response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 400)

    def test_already_added_user_id(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'LINE-U-test-user',
                    }
                }
            }
        }

        # usersテーブルとcognitoの両方にユーザが存在する場合
        with patch('me_external_provider_user_create.UserUtil') as user_mock:
            event['body'] = json.dumps({'user_id': 'username02'})
            user_mock.get_cognito_user_info.return_value = {'Username': 'username02', 'UserAttributes': {}}
            response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 400)

        # usersテーブルのみにユーザが存在する場合(想定されるデータ不整合のため、そのような場合でも意図したエラーを返すことのテスト)
        with patch('me_external_provider_user_create.UserUtil') as user_mock:
            event['body'] = json.dumps({'user_id': 'username02'})
            user_mock.get_cognito_user_info.side_effect = RecordNotFoundError('Record Not Found')
            response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 400)

        # cognitoのみにユーザが存在する場合(想定されるデータ不整合のため、そのような場合でも意図したエラーを返すことのテスト)
        with patch('me_external_provider_user_create.UserUtil') as user_mock:
            event['body'] = json.dumps({'user_id': 'onlycognito'})
            user_mock.get_cognito_user_info.return_value = {'Username': 'onlycognito', 'UserAttributes': {}}
            response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 400)

    def test_invalid_line_user_id(self):
        event = {
            'body': {
                'user_id': 'LINE-test',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'LINE-U-test-user',
                    }
                }
            }
        }

        event['body'] = json.dumps(event['body'])

        response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_invalid_twitter_user_id(self):
        event = {
            'body': {
                'user_id': 'Twitter-test',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'LINE-U-test-user',
                    }
                }
            }
        }

        event['body'] = json.dumps(event['body'])

        response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_invalid_facebook_user_id(self):
        event = {
            'body': {
                'user_id': 'Facebook-test',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'Facebook-U-test-user',
                    }
                }
            }
        }

        event['body'] = json.dumps(event['body'])

        response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_invalid_yahoo_user_id(self):
        event = {
            'body': {
                'user_id': 'Yahoo-test',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'Yahoo-U-test-user',
                    }
                }
            }
        }

        event['body'] = json.dumps(event['body'])

        response = MeExternalProviderUserCreate(event=event, context="", dynamodb=dynamodb).main()
        self.assertEqual(response['statusCode'], 400)
