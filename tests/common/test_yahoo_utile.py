import json
import boto3

from unittest import TestCase
from yahoo_util import YahooUtil
from unittest.mock import MagicMock, patch
from exceptions import YahooOauthError
from exceptions import YahooVerifyException
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')


class TestYahooUtil(TestCase):
    def setUp(self):
        self.yahoo = YahooUtil(
            client_id='fake_client_id',
            secret='fake_secret',
            callback_url='http://callback'
        )

    def test_get_authorization_url_ok(self):
        with patch('yahoo_util.NonceUtil.generate') as nonce_mock:
            nonce_mock.return_value = 'xxxx'
            url = self.yahoo.get_authorization_url(
                dynamodb=dynamodb
            )
            self.assertEqual(
                url,
                'https://auth.login.yahoo.co.jp/yconnect/v2/authorization?response_type=code&client_id=' +
                'fake_client_id&scope=openid%20email%20profile&redirect_uri=http://callback&nonce=xxxx&state=xxxx')

    def test_get_authorization_url_ng_with_clienterror(self):
        with self.assertRaises(ClientError):
            dynamodb.Table = MagicMock()
            dynamodb.Table.return_value.put_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            self.yahoo.get_authorization_url(
                dynamodb=dynamodb
            )

    def test_verify_state_nonce_ok(self):
        with patch('yahoo_util.NonceUtil.verify') as nonce_mock:
            nonce_mock.return_value = True
            response = self.yahoo.verify_state_nonce(
                dynamodb=dynamodb,
                state='xxxx'
            )
            self.assertTrue(response)

    def test_verify_state_nonce_ng(self):
        with self.assertRaises(YahooVerifyException):
            with patch('yahoo_util.NonceUtil.verify') as nonce_mock:
                nonce_mock.return_value = False
                self.yahoo.verify_state_nonce(
                    dynamodb=dynamodb,
                    state='xxxx'
                )

    def test_get_access_token_ok(self):
        with patch('yahoo_util.requests.post') as requests_mock:
            requests_mock.return_value = YahooFakeResponse(
                status_code=200,
                text=json.dumps({
                    'access_token': 'aabbcc',
                })
            )

            token = self.yahoo.get_access_token(
                code='xxxx'
            )

            self.assertEqual(token, {
                'access_token': 'aabbcc',
            })

    def test_get_access_token_ng(self):
        with self.assertRaises(YahooOauthError):
            with patch('yahoo_util.requests.post') as requests_mock:
                requests_mock.return_value = YahooFakeResponse(
                    status_code=400,
                    text=json.dumps({
                        'access_token': 'aabbcc',
                    })
                )

                token = self.yahoo.get_access_token(
                    code='xxxx'
                )

                self.assertEqual(token, {
                    'access_token': 'aabbcc',
                })

    def test_verify_access_token_ok(self):
        with patch('yahoo_util.jwt.decode') as jwt_mock, \
                patch('yahoo_util.jwt.get_unverified_header') as jwt_mock_h, \
                patch('yahoo_util.NonceUtil.verify') as nonce_mock:
            jwt_mock.return_value = {
                'iss': 'https://auth.login.yahoo.co.jp/yconnect/v2',
                'sub': 'user_id',
                'aud': ['ssss-'],
                'exp': 1933325829,
                'iat': 1900906629,
                'amr': ['pwd'],
                'nonce': 'bbbbb',
                'at_hash': 'hrOQHuo3oE6FR82RIiX1SA'
            }
            nonce_mock.return_value = True
            jwt_mock_h.return_value = {
                'kid': '0cc175b9c0f1b6a831c399e269772661'
            }
            response = self.yahoo.verify_access_token(
                dynamodb=dynamodb,
                access_token='access_token',
                id_token='id_token'
            )
            self.assertTrue(response)

    def test_get_user_info_ok(self):
        with patch('yahoo_util.requests.get') as requests_mock:
            requests_mock.return_value = YahooFakeResponse(
                status_code=200,
                text=json.dumps({
                    'sub': 'user_id',
                    'email': 'anyone@alis.to'
                })
            )

            user = self.yahoo.get_user_info(
                access_token='xxxx'
            )

            self.assertEqual(user['user_id'], 'Yahoo-user_id')
            self.assertEqual(user['email'], 'anyone@alis.to')

    def test_get_user_info_ng(self):
        with self.assertRaises(YahooOauthError):
            with patch('yahoo_util.requests.get') as requests_mock:
                requests_mock.return_value = YahooFakeResponse(
                    status_code=400,
                    text=json.dumps({
                        'sub': 'user_id',
                        'email': 'anyone@alis.to'
                    })
                )

                self.yahoo.get_user_info(
                    access_token='xxxx'
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
