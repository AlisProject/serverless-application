import os
import json
from botocore.exceptions import ClientError
from unittest import TestCase
from unittest.mock import patch
from login_facebook_index import LoginFacebookIndex
from exceptions import FacebookOauthError
from tests_util import TestsUtil

dynamodb = TestsUtil.get_dynamodb_client()


class TestLoginFacebookIndex(TestCase):

    def setUp(self):
        os.environ['FACEBOOK_APP_ID'] = 'fake_client_id'
        os.environ['FACEBOOK_APP_SECRET'] = 'fake_secret'
        os.environ['FACEBOOK_APP_TOKEN'] = 'fake_token'
        os.environ['FACEBOOK_OAUTH_CALLBACK_URL'] = 'http://callback'
        os.environ['EXTERNAL_PROVIDER_LOGIN_COMMON_TEMP_PASSWORD'] = 'xxxxxxxx'
        os.environ['EXTERNAL_PROVIDER_LOGIN_MARK'] = 'xxxxx'
        os.environ['COGNITO_USER_POOL_ID'] = 'user_pool_id'
        os.environ['COGNITO_USER_POOL_APP_ID'] = 'user_pool_id'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)
        external_provider_users_items = [
            {
                'external_provider_user_id': 'Facebook-1234',
                'user_display_name': 'test_display_name02',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv'
            },
            {
                'external_provider_user_id': 'Facebook-12345',
                'user_display_name': 'test_display_name02',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'iv': 'iv',
                'user_id': 'user'
            }
        ]
        TestsUtil.create_table(dynamodb, os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'], external_provider_users_items)

    def assert_bad_request(self, params):
        response = LoginFacebookIndex(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_body(self):
        params = {
            'body': {}
        }
        params['body'] = json.dumps(params['body'])
        self.assert_bad_request(params)

    def test_validation_with_no_code(self):
        params = {
            'body': {
                'state': 'state'
            }
        }
        params['body'] = json.dumps(params['body'])
        self.assert_bad_request(params)

    def test_validation_with_no_state(self):
        params = {
            'body': {
                'code': 'code'
            }
        }
        params['body'] = json.dumps(params['body'])
        self.assert_bad_request(params)

    def test_main_ok_with_creating_new_user(self):
        with patch('login_facebook_index.FacebookUtil') as facebook_mock, \
         patch('login_facebook_index.UserUtil') as user_mock, \
         patch('login_facebook_index.CryptoUtil') as crypto_mock:
            facebook_mock.return_value.get_user_info.return_value = {
                'user_id': 'Facebook-1234',
                'email': 'Facebook-1234@example.com',
            }
            facebook_mock.return_value.get_access_token.return_value = {
                'access_token': 'access_token',
                'id_token': 'id_token'
            }
            crypto_mock.encrypt_password.return_value = '&yjgFwFeOpd0{0=&y566'
            facebook_mock.return_value.verify_state_nonce.return_value = True
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
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'Facebook-1234',
                    'has_user_id': False,
                    'status': 'sign_up'
                }
            )

    def test_main_ok_with_existing_user_and_user_id(self):
        with patch('login_facebook_index.FacebookUtil') as facebook_mock, \
         patch('login_facebook_index.UserUtil') as user_mock, patch('login_facebook_index.CryptoUtil') as crypto_mock:
            facebook_mock.return_value.get_user_info.return_value = {
                'user_id': 'Facebook-12345',
                'email': 'Facebook-1234@example.com',
                'display_name': 'my_name'
            }
            facebook_mock.return_value.get_access_token.return_value = {
                'access_token': 'access_token',
                'id_token': 'id_token'
            }
            facebook_mock.return_value.verify_state_nonce.return_value = True

            crypto_mock.get_external_provider_password.return_value = 'password'
            user_mock.exists_user.return_value = True
            user_mock.has_user_id.return_value = True
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
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}, dynamodb=dynamodb).main()
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
        with patch('login_facebook_index.FacebookUtil') as facebook_mock, \
         patch('login_facebook_index.UserUtil') as user_mock, patch('login_facebook_index.CryptoUtil') as crypto_mock:
            facebook_mock.return_value.get_user_info.return_value = {
                'user_id': 'Facebook-1234',
                'email': 'Facebook-1234@example.com',
                'display_name': 'my_name'
            }
            facebook_mock.return_value.get_access_token.return_value = {
                'access_token': 'access_token',
                'id_token': 'id_token'
            }
            facebook_mock.return_value.verify_state_nonce.return_value = True

            crypto_mock.get_external_provider_password.return_value = 'password'
            user_mock.exists_user.return_value = True
            user_mock.has_user_id.return_value = False
            crypto_mock.decrypt_password.return_value = 'password'
            user_mock.external_provider_login.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            params = {
                'body': {
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}, dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'Facebook-1234',
                    'has_user_id': False,
                    'status': 'login'
                }
            )
            user_mock.external_provider_login.assert_called_with(
                cognito=None,
                password='password',
                provider='xxxxx',
                user_id='Facebook-1234',
                user_pool_app_id='user_pool_id',
                user_pool_id='user_pool_id'
            )

    def test_main_ng_with_auth_error(self):
        with patch('login_facebook_index.FacebookUtil') as facebook_mock:
            facebook_mock.return_value.get_user_info.side_effect = FacebookOauthError(
                endpoint='http://example.com',
                status_code=400,
                message='{"error":{"message":"auth error"}}'
            )
            params = {
                'body': {
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 401)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'auth error'
                }
            )

    def test_main_ng_with_facebookexception(self):
        with patch('login_facebook_index.FacebookUtil') as facebook_mock:
            facebook_mock.return_value.get_user_info.side_effect = FacebookOauthError(
                endpoint='http://example.com',
                status_code=500,
                message='error'
            )
            params = {
                'body': {
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )

    def test_main_ng_with_invalid_state_and_existing_user(self):
        with patch('login_facebook_index.FacebookUtil') as facebook_mock, \
         patch('login_facebook_index.UserUtil') as user_mock, patch('login_facebook_index.CryptoUtil') as crypto_mock:
            facebook_mock.return_value.get_user_info.return_value = {
                'user_id': 'facebook-1234',
                'email': 'facebook-1234@example.com',
                'display_name': 'my_name'
            }
            facebook_mock.return_value.get_access_token.return_value = {
                'access_token': 'access_token',
                'id_token': 'id_token'
            }
            facebook_mock.return_value.verify_state_nonce.return_value = False

            crypto_mock.get_external_provider_password.return_value = 'password'
            user_mock.exists_user.return_value = True
            user_mock.has_user_id.return_value = True
            user_mock.external_provider_login.side_effect = ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            )
            params = {
                'body': {
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )

    def test_main_ng_with_awsexception_and_existing_user(self):
        with patch('login_facebook_index.FacebookUtil') as facebook_mock, \
         patch('login_facebook_index.UserUtil') as user_mock:
            facebook_mock.return_value.get_user_info.return_value = {
                'user_id': 'facebook-1234',
                'email': 'facebook-1234@example.com',
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
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )

    def test_main_ng_with_awsexception_and_new_user(self):
        with patch('login_facebook_index.FacebookUtil') as facebook_mock, \
         patch('login_facebook_index.UserUtil') as user_mock, patch('login_facebook_index.CryptoUtil') as crypto_mock:
            facebook_mock.return_value.get_user_info.return_value = {
                'user_id': 'facebook-1234',
                'email': 'facebook-1234@example.com',
                'display_name': 'my_name'
            }
            facebook_mock.return_value.get_access_token.return_value = {
                'access_token': 'access_token',
                'id_token': 'id_token'
            }
            facebook_mock.return_value.verify_state_nonce.return_value = True

            crypto_mock.get_external_provider_password.return_value = 'password'
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
                    'code': 'code',
                    'state': 'state'
                }
            }
            params['body'] = json.dumps(params['body'])
            response = LoginFacebookIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )
