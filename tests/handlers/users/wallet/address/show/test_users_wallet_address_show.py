import os
import boto3
import json
from unittest import TestCase
from unittest.mock import MagicMock
from users_wallet_address_show import UsersWalletAddressShow


class TestUsersWalletAddressShow(TestCase):
    cognito = boto3.client('cognito-idp')
    test_user_id = 'test-user'

    @classmethod
    def setUpClass(cls):
        os.environ['COGNITO_USER_POOL_ID'] = 'xxxxxxx'

    def assert_bad_request(self, params):
        function = UsersWalletAddressShow(params, {}, cognito=self.cognito)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        test_address = '0x401BA17D89D795B3C6e373c5062F1C3F8979e73B'
        self.cognito.admin_get_user = MagicMock(return_value={
            'UserAttributes': [
                {
                    'Name': 'hoge',
                    'Value': 'piyo'
                },
                {
                    'Name': 'custom:private_eth_address',
                    'Value': test_address
                }
            ]
        })
        params = {
            'pathParameters': {
                'user_id': self.test_user_id
            }
        }

        response = UsersWalletAddressShow(params, {}, cognito=self.cognito).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'wallet_address': test_address})

    def test_validation_with_no_user_id_param(self):
        params = {
            'pathParameters': {
            }
        }

        self.assert_bad_request(params)

    def test_validation_user_id_min(self):
        params = {
            'pathParameters': {
                'user_id': 'AA'
            }
        }

        self.assert_bad_request(params)

    def test_validation_user_id_max(self):
        params = {
            'pathParameters': {
                'user_id': 'A' * 51
            }
        }

        self.assert_bad_request(params)
