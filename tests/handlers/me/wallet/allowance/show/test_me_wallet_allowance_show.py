import boto3
import json
from unittest import TestCase
from me_wallet_allowance_show import MeWalletAllowanceShow
from unittest.mock import patch, MagicMock


class TestMeWalletAllowanceShow(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

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
        test_allowance = '0x10'
        magic_lib = MagicMock(return_value=test_allowance)
        with patch('private_chain_util.PrivateChainUtil.get_allowance', magic_lib):
            response = MeWalletAllowanceShow(params, {}, dynamodb=self.dynamodb).main()
            self.assertEqual(200, response['statusCode'])
            self.assertEqual({'allowance': test_allowance}, json.loads(response['body']))

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
        response = MeWalletAllowanceShow(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(200, response['statusCode'])
        self.assertEqual({'allowance': '0x0'}, json.loads(response['body']))
