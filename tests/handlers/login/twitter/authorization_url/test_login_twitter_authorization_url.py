import os
import json
from botocore.exceptions import ClientError
from unittest import TestCase
from unittest.mock import patch
from login_twitter_authorization_url import LoginTwitterAuthorizationUrl


class TestLoginTwitterAuthorizationUrl(TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['TWITTER_CONSUMER_KEY'] = 'fake_twitter_consumer_key'
        os.environ['TWITTER_CONSUMER_SECRET'] = 'fake_twitter_consumer_secret'
        os.environ['TWITTER_OAUTH_CALLBACK_URL'] = 'http://localhost'

    def test_exec_main_ok(self):
        with patch('login_twitter_authorization_url.TwitterUtil') as twitter_mock:
            twitter_mock.return_value.generate_auth_url.return_value = 'oauth_url'
            response = LoginTwitterAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {'url': 'oauth_url'}
            )

    def test_exec_main_ng(self):
        with patch('login_twitter_authorization_url.TwitterUtil') as twitter_mock:
            twitter_mock.return_value.generate_auth_url.side_effect = ClientError(
                {'Error': {'Code': 'UserNotFoundException'}},
                'operation_name'
            )

            response = LoginTwitterAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {'message': 'Internal server error'}
            )
