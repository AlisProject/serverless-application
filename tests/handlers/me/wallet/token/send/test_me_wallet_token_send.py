import os
import json
import re
import settings
from decimal import Decimal
from unittest import TestCase
from me_wallet_token_send import MeWalletTokenSend
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeWalletTokenSend(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_aws_auth_to_env()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        TestsUtil.create_table(self.dynamodb, os.environ['TOKEN_SEND_TABLE_NAME'], [])

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeWalletTokenSend(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok(self):
        with patch('private_chain_util.PrivateChainUtil.send_transaction') \
            as mock_send_transaction, \
            patch('private_chain_util.PrivateChainUtil.validate_transaction_completed') \
                as mock_validate_transaction_completed:
            # mock の初期化
            return_allowance = "0x0"
            return_get_transaction_count = "0x0"
            return_approve = "0x1111000000000000000000000000000000000000"
            return_relay = "0x2222000000000000000000000000000000000000"
            mock_send_transaction.side_effect = [
                return_allowance,
                return_get_transaction_count,
                return_approve,
                return_relay
            ]
            mock_validate_transaction_completed.return_value = True

            # テスト対象実施
            target_token_send_value = str(settings.parameters['token_send_value']['minimum'])
            private_eth_address = '0x3000000000000000000000000000000000000000'
            recipient_eth_address = '0x2000000000000000000000000000000000000000'
            event = {
                'body': {
                    'recipient_eth_address': '0x2000000000000000000000000000000000000000',
                    'send_value': target_token_send_value
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': private_eth_address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 200)

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(target_token_send_value),
                'approve_transaction': return_approve,
                'relay_transaction_hash': return_relay,
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003))
            }
            self.assertEqual(expected_token_send, token_send_itmes[0])

            # 各種メソッド呼び出し確認
            # send_transaction
            self.assertEqual(len(mock_send_transaction.call_args_list), 4)
            args_allowance = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/allowance',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address,
                    'owner_eth_address': private_eth_address[2:],
                    'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[0][1], args_allowance)
            args_get_transaction_count = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/get_transaction_count',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[1][1], args_get_transaction_count)
            args_approve = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/approve',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address,
                    'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:],
                    'nonce': '0x0',
                    'value': format(int(target_token_send_value), '064x')
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[2][1], args_approve)
            args_relay = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/relay',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address,
                    'recipient_eth_address': recipient_eth_address[2:],
                    'nonce': '0x1',
                    'amount': format(int(target_token_send_value), '064x')
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[3][1], args_relay)
            # validate_transaction_completed
            self.assertEqual(len(mock_validate_transaction_completed.call_args_list), 2)
            self.assertEqual(mock_validate_transaction_completed.call_args_list[0][0], (return_approve,))
            self.assertEqual(mock_validate_transaction_completed.call_args_list[1][0], (return_relay,))

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_exists_allowance(self):
        with patch('private_chain_util.PrivateChainUtil.send_transaction') \
            as mock_send_transaction, \
            patch('private_chain_util.PrivateChainUtil.validate_transaction_completed') \
                as mock_validate_transaction_completed:
            # mock の初期化
            return_allowance = "0x1"
            return_get_transaction_count = "0x0"
            return_approve_zero = "0x0000000000000000000000000000000000000000"
            return_approve = "0x1111000000000000000000000000000000000000"
            return_relay = "0x2222000000000000000000000000000000000000"
            mock_send_transaction.side_effect = [
                return_allowance,
                return_get_transaction_count,
                return_approve_zero,
                return_approve,
                return_relay
            ]
            mock_validate_transaction_completed.return_value = True

            # テスト対象実施
            target_token_send_value = str(settings.parameters['token_send_value']['maximum'])
            private_eth_address = '0x3000000000000000000000000000000000000000'
            recipient_eth_address = '0x2000000000000000000000000000000000000000'
            event = {
                'body': {
                    'recipient_eth_address': '0x2000000000000000000000000000000000000000',
                    'send_value': target_token_send_value
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': private_eth_address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 200)

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(target_token_send_value),
                'approve_transaction': return_approve,
                'relay_transaction_hash': return_relay,
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003))
            }
            self.assertEqual(expected_token_send, token_send_itmes[0])

            # 各種メソッド呼び出し確認
            # send_transaction
            self.assertEqual(len(mock_send_transaction.call_args_list), 5)
            args_allowance = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/allowance',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address,
                    'owner_eth_address': private_eth_address[2:],
                    'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[0][1], args_allowance)
            args_get_transaction_count = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/get_transaction_count',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[1][1], args_get_transaction_count)
            args_approve_zero = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/approve',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address,
                    'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:],
                    'nonce': '0x0',
                    'value': format(0, '064x')
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[2][1], args_approve_zero)
            args_approve = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/approve',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address,
                    'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:],
                    'nonce': '0x1',
                    'value': format(int(target_token_send_value), '064x')
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[3][1], args_approve)
            args_relay = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/relay',
                'payload_dict': {
                    'from_user_eth_address': private_eth_address,
                    'recipient_eth_address': recipient_eth_address[2:],
                    'nonce': '0x2',
                    'amount': format(int(target_token_send_value), '064x')
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[4][1], args_relay)
            # validate_transaction_completed
            self.assertEqual(len(mock_validate_transaction_completed.call_args_list), 3)
            self.assertEqual(mock_validate_transaction_completed.call_args_list[0][0], (return_approve_zero,))
            self.assertEqual(mock_validate_transaction_completed.call_args_list[1][0], (return_approve,))
            self.assertEqual(mock_validate_transaction_completed.call_args_list[2][0], (return_relay,))

    def test_main_ng_less_than_min_value(self):
        target_token_send_value = str(settings.parameters['token_send_value']['minimum'] - 1)
        event = {
            'body': {
                'recipient_eth_address': '0x2000000000000000000000000000000000000000',
                'send_value': target_token_send_value
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user_01',
                        'custom:private_eth_address': '0x3000000000000000000000000000000000000000',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])

        response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        items = token_send_table_name.scan()['Items']
        self.assertEqual(len(items), 0)

    def test_main_ng_minus_value(self):
        target_token_send_value = '-1'
        event = {
            'body': {
                'recipient_eth_address': '0x2000000000000000000000000000000000000000',
                'send_value': target_token_send_value
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user_01',
                        'custom:private_eth_address': '0x3000000000000000000000000000000000000000',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])

        response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        items = token_send_table_name.scan()['Items']
        self.assertEqual(len(items), 0)

    def test_main_ng_greater_than_max_value(self):
        target_token_send_value = str(settings.parameters['token_send_value']['maximum'] + 1)
        event = {
            'body': {
                'recipient_eth_address': '0x2000000000000000000000000000000000000000',
                'send_value': target_token_send_value
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user_01',
                        'custom:private_eth_address': '0x3000000000000000000000000000000000000000',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])

        response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        items = token_send_table_name.scan()['Items']
        self.assertEqual(len(items), 0)

    def test_main_ng_not_number_for_value(self):
        target_token_send_value = 'aaaaaaaaaaaaa'
        event = {
            'body': {
                'recipient_eth_address': '0x2000000000000000000000000000000000000000',
                'send_value': target_token_send_value
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user_01',
                        'custom:private_eth_address': '0x3000000000000000000000000000000000000000',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])

        response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        items = token_send_table_name.scan()['Items']
        self.assertEqual(len(items), 0)

    def test_main_ng_not_string_for_eth_address(self):
        target_token_send_value = str(settings.parameters['token_send_value']['minimum'])
        event = {
            'body': {
                'recipient_eth_address': 0x2000000000000000000000000000000000000000,
                'send_value': target_token_send_value
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user_01',
                        'custom:private_eth_address': '0x3000000000000000000000000000000000000000',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])

        response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        items = token_send_table_name.scan()['Items']
        self.assertEqual(len(items), 0)

    def test_main_ng_not_match_pattern_for_eth_address(self):
        target_token_send_value = str(settings.parameters['token_send_value']['minimum'])
        event = {
            'body': {
                'recipient_eth_address': '0x200000000000000000000000000000000000ZZZZ',
                'send_value': target_token_send_value
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user_01',
                        'custom:private_eth_address': '0x3000000000000000000000000000000000000000',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])

        response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        items = token_send_table_name.scan()['Items']
        self.assertEqual(len(items), 0)
