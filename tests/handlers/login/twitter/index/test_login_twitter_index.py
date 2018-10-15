import os
import json
from botocore.exceptions import ClientError
from unittest import TestCase
from unittest.mock import patch
from login_twitter_index import LoginTwitterIndex
from exceptions import TwitterOauthError
from tests_util import TestsUtil

dynamodb = TestsUtil.get_dynamodb_client()


class TestLoginTwitterIndex(TestCase):

    def setUp(self):
        os.environ['TWITTER_CONSUMER_KEY'] = 'fake_twitter_consumer_key'
        os.environ['TWITTER_CONSUMER_SECRET'] = 'fake_twitter_consumer_secret'
        os.environ['EXTERNAL_PROVIDER_LOGIN_COMMON_TEMP_PASSWORD'] = 'xxxxxxxxxx'
        os.environ['EXTERNAL_PROVIDER_LOGIN_MARK'] = 'xxxxx'
        os.environ['COGNITO_USER_POOL_ID'] = 'user_pool_id'
        os.environ['COGNITO_USER_POOL_APP_ID'] = 'user_pool_id'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)
        external_provider_users_items = [
            {
                'external_provider_user_id': 'Twitter-1234',
                'user_display_name': 'test_display_name02',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv',
                'icon_image_url': 'https://xxxxxxxx'
            },
            {
                'external_provider_user_id': 'Twitter-12345',
                'user_display_name': 'test_display_name02',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv',
                'icon_image_url': 'https://xxxxxxxx',
                'user_id': 'user'
            }
        ]
        TestsUtil.create_table(dynamodb, os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'], external_provider_users_items)

    def assert_bad_request(self, params):
        response = LoginTwitterIndex(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_body(self):
        params = {
            'body': {}
        }
        params['body'] = json.dumps(params['body'])
        self.assert_bad_request(params)

    def test_validation_with_no_oauth_token(self):
        params = {
            'body': {
                'oauth_verifier': 'fake_oauth_verifier'
            }
        }
        params['body'] = json.dumps(params['body'])
        self.assert_bad_request(params)

    def test_validation_with_no_oauth_verifier(self):
        params = {
            'body': {
                'oauth_token': 'fake_oauth_token'
            }
        }
        params['body'] = json.dumps(params['body'])
        self.assert_bad_request(params)

    def test_main_ok_with_creating_new_user(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock, \
         patch('login_twitter_index.UserUtil') as user_mock:
            twitter_mock.return_value.get_user_info.return_value = {
                'user_id': 'Twitter-1234',
                'email': 'Twitter-1234@example.com',
                'display_name': 'my_name',
                'icon_image_url': 'http://example.com/image'
            }
            user_mock.exists_user.return_value = False
            user_mock.create_external_provider_user.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            user_mock.add_external_provider_user_info.return_value = None
            params = {
                'body': {
                    'oauth_token': 'fake_oauth_token',
                    'oauth_verifier': 'fake_oauth_verifier'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginTwitterIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'Twitter-1234',
                    'has_user_id': False,
                    'status': 'sign_up'
                }
            )

    def test_main_ok_with_existing_user_and_user_id(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock, \
         patch('login_twitter_index.UserUtil') as user_mock:
            twitter_mock.return_value.get_user_info.return_value = {
                'user_id': 'Twitter-12345',
                'email': 'Twitter-1234@example.com',
                'display_name': 'my_name',
                'icon_image_url': 'http://example.com/image'
            }
            user_mock.exists_user.return_value = True
            user_mock.has_user_id.return_value = True
            user_mock.decrypt_password.return_value = 'password'
            user_mock.get_user_id.return_value = 'user_id'
            user_mock.external_provider_login.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            params = {
                'body': {
                    'oauth_token': 'fake_oauth_token',
                    'oauth_verifier': 'fake_oauth_verifier'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginTwitterIndex(params, {}, dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'user_id',
                    'has_user_id': True,
                    'status': 'login'
                }
            )
            user_mock.external_provider_login.assert_called_with(
                cognito=None,
                password='password',
                provider='xxxxx',
                user_id='user_id',
                user_pool_app_id='user_pool_id',
                user_pool_id='user_pool_id'
            )

    def test_main_ok_with_existing_user_and_no_user_id(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock, \
         patch('login_twitter_index.UserUtil') as user_mock:
            twitter_mock.return_value.get_user_info.return_value = {
                'user_id': 'Twitter-1234',
                'email': 'Twitter-1234@example.com',
                'display_name': 'my_name',
                'icon_image_url': 'http://example.com/image'
            }
            user_mock.exists_user.return_value = True
            user_mock.has_user_id.return_value = False
            user_mock.decrypt_password.return_value = 'password'
            user_mock.external_provider_login.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            params = {
                'body': {
                    'oauth_token': 'fake_oauth_token',
                    'oauth_verifier': 'fake_oauth_verifier'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginTwitterIndex(params, {}, dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'Twitter-1234',
                    'has_user_id': False,
                    'status': 'login'
                }
            )
            user_mock.external_provider_login.assert_called_with(
                cognito=None,
                password='password',
                provider='xxxxx',
                user_id='Twitter-1234',
                user_pool_app_id='user_pool_id',
                user_pool_id='user_pool_id'
            )

    def test_main_ng_with_auth_error(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock:
            twitter_mock.return_value.get_user_info.side_effect = TwitterOauthError(
                endpoint='http://example.com',
                status_code=401,
                message='auth error'
            )
            params = {
                'body': {
                    'oauth_token': 'fake_oauth_token',
                    'oauth_verifier': 'fake_oauth_verifier'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginTwitterIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 401)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'auth error'
                }
            )

    def test_main_ng_with_twitterexception(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock:
            twitter_mock.return_value.get_user_info.side_effect = TwitterOauthError(
                endpoint='http://example.com',
                status_code=500,
                message='error'
            )
            params = {
                'body': {
                    'oauth_token': 'fake_oauth_token',
                    'oauth_verifier': 'fake_oauth_verifier'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginTwitterIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )

    def test_main_ng_with_awsexception_and_existing_user(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock, \
         patch('login_twitter_index.UserUtil') as user_mock:
            twitter_mock.return_value.get_user_info.return_value = {
                'user_id': 'Twitter-1234',
                'email': 'Twitter-1234@example.com',
                'display_name': 'my_name'
            }
            user_mock.exists_user.return_value = True
            user_mock.has_user_id.return_value = True
            user_mock.external_provider_login.side_effect = ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            )
            params = {
                'body': {
                    'oauth_token': 'fake_oauth_token',
                    'oauth_verifier': 'fake_oauth_verifier'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginTwitterIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )

    def test_main_ng_with_awsexception_and_new_user(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock, \
         patch('login_twitter_index.UserUtil') as user_mock:
            twitter_mock.return_value.get_user_info.return_value = {
                'user_id': 'Twitter-1234',
                'email': 'Twitter-1234@example.com',
                'display_name': 'my_name'
            }
            user_mock.exists_user.return_value = False
            user_mock.create_external_provider_user.return_value = ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            )
            user_mock.force_non_verified_phone.return_value = None
            user_mock.add_user_profile.return_value = None
            user_mock.add_external_provider_user_info.return_value = None
            user_mock.has_user_id.return_value = True
            params = {
                'body': {
                    'oauth_token': 'fake_oauth_token',
                    'oauth_verifier': 'fake_oauth_verifier'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginTwitterIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )
