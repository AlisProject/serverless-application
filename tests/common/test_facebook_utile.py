import json
import boto3

from unittest import TestCase
from facebook_util import FacebookUtil
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from exceptions import FacebookVerifyException
from exceptions import FacebookOauthError

dynamodb = boto3.resource('dynamodb')


class TestFacebookUtil(TestCase):
    def setUp(self):
        self.fb = FacebookUtil(
            app_id='fake_client_id',
            app_secret='fake_secret',
            callback_url='http://callback'
        )

    def test_remove_postfix_str_from_state_token_ok(self):
        self.assertEqual(
            'ssssss',
            self.fb.remove_postfix_str_from_state_token('ssssss#_=_')
        )

    def test_remove_postfix_str_from_state_token_ok_with_do_nothing(self):
        self.assertEqual(
            'aaaaa',
            self.fb.remove_postfix_str_from_state_token('aaaaa')
        )

    def test_get_authorization_url_ok(self):
        with patch('facebook_util.NonceUtil.generate') as nonce_mock:
            nonce_mock.return_value = 'xxxx'
            url = self.fb.get_authorization_url(
                dynamodb=dynamodb
            )
            self.assertEqual(url, 'https://www.facebook.com/dialog/oauth?client_id=fake_client_id&redirect_uri=http://callback&scope=email&state=xxxx')

    def test_get_authorization_url_ng_with_clienterror(self):
        with self.assertRaises(ClientError):
            dynamodb.Table = MagicMock()
            dynamodb.Table.return_value.put_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            self.fb.get_authorization_url(
                dynamodb=dynamodb
            )

    def test_verify_state_nonce_ok(self):
        with patch('facebook_util.NonceUtil.verify') as nonce_mock:
            nonce_mock.return_value = True
            response = self.fb.verify_state_nonce(
                dynamodb=dynamodb,
                state='xxxx'
            )
            self.assertTrue(response)

    def test_verify_state_nonce_ng(self):
        with self.assertRaises(FacebookVerifyException):
            with patch('facebook_util.NonceUtil.verify') as nonce_mock:
                nonce_mock.return_value = False
                self.fb.verify_state_nonce(
                    dynamodb=dynamodb,
                    state='xxxx'
                )

    def test_get_access_token_ok(self):
        with patch('facebook_util.requests.get') as requests_mock:
            requests_mock.return_value = FacebookFakeResponse(
                status_code=200,
                text=json.dumps({
                    'access_token': 'aabbcc',
                })
            )

            token = self.fb.get_access_token(
                code='xxxx'
            )

            self.assertEqual(token, 'aabbcc')

    def test_get_access_token_ng(self):
        with self.assertRaises(FacebookOauthError):
            with patch('facebook_util.requests.get') as requests_mock:
                requests_mock.return_value = FacebookFakeResponse(
                    status_code=400,
                    text='error'
                )

                self.fb.get_access_token(
                    code='xxxx'
                )

    def test_get_user_info_ok(self):
        with patch('facebook_util.requests.get') as requests_mock, \
         patch.object(self.fb, '_FacebookUtil__verify_access_token', return_value=True):
            requests_mock.return_value = FacebookFakeResponse(
                status_code=200,
                text=json.dumps({
                    'id': 'xxxxxx',
                    'email': 'anyone@alis.io'
                })
            )

            user = self.fb.get_user_info(
                access_token='xxxx'
            )
            self.assertEqual(user['user_id'], 'Facebook-xxxxxx')
            self.assertEqual(user['email'], 'anyone@alis.io')

    def test_get_user_info_ok_with_example_email(self):
        with patch('facebook_util.requests.get') as requests_mock, \
         patch.object(self.fb, '_FacebookUtil__verify_access_token', return_value=True):
            requests_mock.return_value = FacebookFakeResponse(
                status_code=200,
                text=json.dumps({
                    'id': 'xxxxxx'
                })
            )

            user = self.fb.get_user_info(
                access_token='xxxx'
            )
            self.assertEqual(user['user_id'], 'Facebook-xxxxxx')
            self.assertEqual(user['email'], 'Facebook-xxxxxx@example.com')

    def test_get_user_info_ng_with_oauth_error(self):
        with self.assertRaises(FacebookOauthError):
            with patch('facebook_util.requests.get') as requests_mock, \
                 patch.object(self.fb, '_FacebookUtil__verify_access_token', return_value=True):
                    requests_mock.return_value = FacebookFakeResponse(
                        status_code=400,
                        text=json.dumps({
                            'id': 'xxxxxx'
                        })
                    )

                    self.fb.get_user_info(
                        access_token='xxxx'
                    )

    def test_get_user_info_ng_with_verify_error(self):
        with self.assertRaises(FacebookVerifyException):
            with patch('facebook_util.requests.get') as requests_mock, \
                 patch.object(self.fb, '_FacebookUtil__verify_access_token', return_value=False):
                    requests_mock.return_value = FacebookFakeResponse(
                        status_code=200,
                        text=json.dumps({
                            'id': 'xxxxxx'
                        })
                    )

                    self.fb.get_user_info(
                        access_token='xxxx'
                    )


class FacebookFakeResponse:
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
