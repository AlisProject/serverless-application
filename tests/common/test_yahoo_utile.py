import json
import boto3

from unittest import TestCase
from yahoo_util import YahooUtil
from unittest.mock import MagicMock, patch
from exceptions import YahooOauthError
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')


class TestYahooUtil(TestCase):
    def setUp(self):
        self.yahoo = YahooUtil(
            client_id='fake_client_id',
            secret='fake_secret'
        )

    def test_get_authorization_url_ok(self):
        with patch('yahoo_util.NonceUtil.generate') as nonce_mock:
            nonce_mock.return_value = 'xxxx'
            url = self.yahoo.get_authorization_url(
                dynamodb=dynamodb,
                callback_url='http://callback'
            )
            self.assertEqual(url, 'https://auth.login.yahoo.co.jp/yconnect/v2/authorization?response_type=code&client_id=fake_client_id&scope=openid%20email%20profile&redirect_uri=http://callback&nonce=xxxx&state=xxxx')

    def test_get_authorization_url_ng_with_clienterror(self):
        with self.assertRaises(ClientError):
            dynamodb.Table = MagicMock()
            dynamodb.Table.return_value.put_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            self.yahoo.get_authorization_url(
                dynamodb=dynamodb,
                callback_url='http://callback'
            )


class YahooFakeResponse:
    def __init__(self, status_code, content='', text=''):
        self._status_code = status_code
        self._content = content
        self._text = text

    def get_status_code(self):
        return self._status_code

    def get_content(self):
        return self._content

    def get_text(self):
        return self._text
    status_code = property(get_status_code)
    content = property(get_content)
    text = property(get_text)
