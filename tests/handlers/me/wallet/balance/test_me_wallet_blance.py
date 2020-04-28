import os
import json
from unittest import TestCase
from me_wallet_balance import MeWalletBalance
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeWalletBalance(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        user_configurations_items = [
            {
                'user_id': 'test-user',
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            },
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'], user_configurations_items)

    def test_main_ok(self):
        test_address = '0x5d7743a4a6f21593ff6d3d81595f270123456789'
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test-user',
                        'custom:private_eth_address': test_address
                    }
                }
            }
        }
        test_balance = '0x10'
        magic_lib = MagicMock(return_value=test_balance)
        with patch('private_chain_util.PrivateChainUtil.get_balance', magic_lib):
            response = MeWalletBalance(params, {}, dynamodb=self.dynamodb).main()
            self.assertEqual(200, response['statusCode'])
            self.assertEqual({'result': test_balance}, json.loads(response['body']))

            args, _ = magic_lib.call_args
            self.assertEqual(test_address, args[0])

    def test_main_ok_not_exists_private_eth_address(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test-user'
                    }
                }
            }
        }
        response = MeWalletBalance(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(200, response['statusCode'])
        self.assertEqual({'result': '0x0'}, json.loads(response['body']))

    def test_main_return_zero_if_user_have_not_migrated(self):
        test_address = '0x5d7743a4a6f21593ff6d3d81595f270123456789'
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'not-migrated-user',
                        'custom:private_eth_address': test_address
                    }
                }
            }
        }

        test_balance = '0x10'
        magic_lib = MagicMock(return_value=test_balance)
        with patch('private_chain_util.PrivateChainUtil.get_balance', magic_lib):
            response = MeWalletBalance(params, {}, dynamodb=self.dynamodb).main()
            self.assertEqual(200, response['statusCode'])
            self.assertEqual({'result': '0x0'}, json.loads(response['body']))
