import os
import json
from botocore.exceptions import ClientError
from unittest import TestCase
from unittest.mock import patch
from login_twitter_index import LoginTwitterIndex
from exceptions import TwitterOauthError


class TestLoginTwitterIndex(TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['TWITTER_CONSUMER_KEY'] = 'fake_twitter_consumer_key'
        os.environ['TWITTER_CONSUMER_SECRET'] = 'fake_twitter_consumer_secret'
        os.environ['TWITTER_LOGIN_COMMON_TEMP_PASSWORD'] = 'xxxxxxxxxx'
        os.environ['THIRD_PARTY_LOGIN'] = 'xxxxx'
        os.environ['COGNITO_USER_POOL_ID'] = 'user_pool_id'
        os.environ['COGNITO_USER_POOL_APP_ID'] = 'user_pool_id'

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
            user_mock.create_sns_user.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            user_mock.force_non_verified_phone.return_value = None
            user_mock.update_user_profile.return_value = None
            user_mock.add_sns_user_info.return_value = None
            user_mock.has_alias_user_id.return_value = True
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
                    'has_alias_user_id': True,
                    'status': 'sign_up'
                }
            )

    def test_main_ok_with_existing_user(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock, \
         patch('login_twitter_index.UserUtil') as user_mock:
            twitter_mock.return_value.get_user_info.return_value = {
                'user_id': 'Twitter-1234',
                'email': 'Twitter-1234@example.com',
                'display_name': 'my_name',
                'icon_image_url': 'http://example.com/image'
            }
            user_mock.exists_user.return_value = True
            user_mock.has_alias_user_id.return_value = True
            user_mock.sns_login.return_value = {
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
            response = LoginTwitterIndex(params, {}).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'has_alias_user_id': True,
                    'status': 'login'
                }
            )

    def test_main_ng_with_twitterexception(self):
        with patch('login_twitter_index.TwitterUtil') as twitter_mock:
            twitter_mock.return_value.get_user_info.side_effect = TwitterOauthError('error')
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
            user_mock.has_alias_user_id.return_value = True
            user_mock.sns_login.side_effect = ClientError(
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
            user_mock.create_sns_user.return_value = ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            )
            user_mock.force_non_verified_phone.return_value = None
            user_mock.update_user_profile.return_value = None
            user_mock.add_sns_user_info.return_value = None
            user_mock.has_alias_user_id.return_value = True
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
