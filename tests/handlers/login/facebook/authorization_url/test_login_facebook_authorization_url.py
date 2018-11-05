import os
import json
from botocore.exceptions import ClientError
from unittest import TestCase
from unittest.mock import patch
from exceptions import FacebookOauthError
from login_facebook_authorization_url import LoginFacebookAuthorizationUrl


class TestLoginFacebookAuthorizationUrl(TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['FACEBOOK_APP_ID'] = 'fake_facebook_consumer_key'
        os.environ['FACEBOOK_APP_SECRET'] = 'fake_facebook_consumer_secret'
        os.environ['FACEBOOK_OAUTH_CALLBACK_URL'] = 'http://localhost'
        os.environ['FACEBOOK_APP_TOKEN'] = 'fake_facebook_token'

    def test_exec_main_ok(self):
        with patch('login_facebook_authorization_url.FacebookUtil') as fb_mock:
            fb_mock.return_value.get_authorization_url.return_value = 'oauth_url'
            response = LoginFacebookAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {'url': 'oauth_url'}
            )

    def test_exec_main_ng_with_clienterror(self):
        with patch('login_facebook_authorization_url.FacebookUtil') as fb_mock:
            fb_mock.return_value.generate_auth_url.side_effect = ClientError(
                {'Error': {'Code': 'UserNotFoundException'}},
                'operation_name'
            )
            response = LoginFacebookAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {'message': 'Internal server error'}
            )

    def test_exec_main_ng_with_fberror(self):
        with patch('login_facebook_authorization_url.FacebookUtil') as fb_mock:
            fb_mock.return_value.generate_auth_url.side_effect = FacebookOauthError(
                endpoint='http://example.com',
                status_code=400,
                message='error'
            )
            response = LoginFacebookAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {'message': 'Internal server error'}
            )
