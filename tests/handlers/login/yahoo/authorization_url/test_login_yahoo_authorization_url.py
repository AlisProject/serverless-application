import os
import json
from botocore.exceptions import ClientError
from unittest import TestCase
from unittest.mock import patch
from exceptions import YahooOauthError
from login_yahoo_authorization_url import LoginYahooAuthorizationUrl


class TestLoginYahooAuthorizationUrl(TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['YAHOO_CLIENT_ID'] = 'fake_yahoo_consumer_key'
        os.environ['YAHOO_SECRET'] = 'fake_yahoo_consumer_secret'
        os.environ['YAHOO_OAUTH_CALLBACK_URL'] = 'http://localhost'

    def test_exec_main_ok(self):
        with patch('login_yahoo_authorization_url.YahooUtil') as yahoo_mock:
            yahoo_mock.return_value.get_authorization_url.return_value = 'oauth_url'
            response = LoginYahooAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {'url': 'oauth_url'}
            )

    def test_exec_main_ng_with_clienterror(self):
        with patch('login_yahoo_authorization_url.YahooUtil') as yahoo_mock:
            yahoo_mock.return_value.generate_auth_url.side_effect = ClientError(
                {'Error': {'Code': 'UserNotFoundException'}},
                'operation_name'
            )
            response = LoginYahooAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {'message': 'Internal server error'}
            )

    def test_exec_main_ng_with_yahoo(self):
        with patch('login_yahoo_authorization_url.YahooUtil') as yahoo_mock:
            yahoo_mock.return_value.generate_auth_url.side_effect = YahooOauthError(
                endpoint='http://example.com',
                status_code=400,
                message='error'
            )
            response = LoginYahooAuthorizationUrl({}, {}).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {'message': 'Internal server error'}
            )
