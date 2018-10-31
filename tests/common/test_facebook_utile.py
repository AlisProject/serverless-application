import json
import boto3

from unittest import TestCase
from facebook_util import FacebookUtil
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')


class TestFacebookUtil(TestCase):
    def setUp(self):
        self.fb = FacebookUtil(
            app_id='fake_client_id',
            app_secret='fake_secret'
        )

    def test_get_authorization_url_ok(self):
        with patch('facebook_util.NonceUtil.generate') as nonce_mock:
            nonce_mock.return_value = 'xxxx'
            url = self.fb.get_authorization_url(
                dynamodb=dynamodb,
                callback_url='http://callback'
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
                dynamodb=dynamodb,
                callback_url='http://callback'
            )
