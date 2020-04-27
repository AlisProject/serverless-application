import os
import json
import re
import settings
from decimal import Decimal
from unittest import TestCase
from me_wallet_token_send import MeWalletTokenSend
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from exceptions import SendTransactionError, ReceiptError
from botocore.exceptions import ClientError
from web3 import Web3, HTTPProvider
from private_chain_util import PrivateChainUtil


class TestMeWalletTokenSend(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_aws_auth_to_env()
        TestsUtil.set_all_private_chain_valuables_to_env()
        cls.web3 = Web3(HTTPProvider('http://localhost:8584'))
        cls.test_account = cls.web3.eth.account.create()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        TestsUtil.create_table(self.dynamodb, os.environ['TOKEN_SEND_TABLE_NAME'], [])
        os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE'] = '100000000000000000000000'

        user_configurations_items = [
            {
                'user_id': 'user_01',
                'private_eth_address': self.test_account.address
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'], user_configurations_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeWalletTokenSend(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['approve_transaction_hash', 'relay_transaction_hash']))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ok(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count, \
                patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed:

            # mock の初期化
            mock_get_allowance.return_value = '0x' + '0' * 64
            mock_get_transaction_count.return_value = format(nonce, '#x')
            mock_is_transaction_completed.return_value = True

            # テスト実施
            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
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
            self.assertEqual(json.loads(response['body']), {'is_completed': True})

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(send_value),
                'approve_transaction': 'approve_transaction_hash',
                'relay_transaction_hash': 'relay_transaction_hash',
                'send_status': 'done',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003))
            }
            self.assertEqual(expected_token_send, token_send_itmes[0])

            # 各種メソッド呼び出し確認
            # mock_get_allowance
            self.assertEqual(mock_get_allowance.call_count, 1)
            args, _ = mock_get_allowance.call_args
            self.assertEqual(args[0], self.test_account.address)
            # get_transaction_count
            self.assertEqual(mock_get_transaction_count.call_count, 1)
            args, _ = mock_get_transaction_count.call_args
            self.assertEqual(args[0], self.test_account.address)
            # is_transaction_completed
            self.assertEqual(mock_is_transaction_completed.call_count, 1)
            args, _ = mock_is_transaction_completed.call_args
            self.assertEqual(args[0], 'relay_transaction_hash')

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['init_hash', 'approve_transaction_hash', 'relay_transaction_hash']))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ok_exists_allowance_with_status_doing(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        init_transaction = self.create_singed_approve_transaction(nonce, 0)
        approve_transaction = self.create_singed_approve_transaction(nonce + 1, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 2, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count, \
                patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed:

            # mock の初期化
            mock_get_allowance.return_value = '0x1'
            mock_get_transaction_count.return_value = format(nonce, '#x')
            mock_is_transaction_completed.return_value = False

            # テスト実施
            event = {
                'body': {
                    'init_approve_signed_transaction': init_transaction,
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
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
            self.assertEqual(json.loads(response['body']), {'is_completed': False})

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(send_value),
                'approve_transaction': 'approve_transaction_hash',
                'relay_transaction_hash': 'relay_transaction_hash',
                'send_status': 'doing',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003))
            }
            self.assertEqual(expected_token_send, token_send_itmes[0])

            # 各種メソッド呼び出し確認
            # mock_get_allowance
            self.assertEqual(mock_get_allowance.call_count, 1)
            args, _ = mock_get_allowance.call_args
            self.assertEqual(args[0], self.test_account.address)
            # get_transaction_count
            self.assertEqual(mock_get_transaction_count.call_count, 1)
            args, _ = mock_get_transaction_count.call_args
            self.assertEqual(args[0], self.test_account.address)
            # is_transaction_completed
            self.assertEqual(mock_is_transaction_completed.call_count, 1)
            args, _ = mock_is_transaction_completed.call_args
            self.assertEqual(args[0], 'relay_transaction_hash')

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['approve_transaction_hash', 'relay_transaction_hash']))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000100))
    @patch('time.time', MagicMock(return_value=1520150552.000100))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ok_exists_token_send_info_with_fail_data(self):
        # 実行前データを作成
        user_id = 'user_01'
        items = [
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x1100000000000000000000000000000000000000',
                'relay_transaction_hash': '0x2200000000000000000000000000000000000000',
                'send_status': 'done',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000010),
                'created_at': Decimal(int(1520150552.000010))
            },
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x3300000000000000000000000000000000000000',
                'relay_transaction_hash': '0x4400000000000000000000000000000000000000',
                'send_status': 'done',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000020),
                'created_at': Decimal(int(1520150552.000020))
            },
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x5500000000000000000000000000000000000000',
                'relay_transaction_hash': '0x6600000000000000000000000000000000000000',
                'send_status': 'doing',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000030),
                'created_at': Decimal(int(1520150552.000030))
            },
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x7700000000000000000000000000000000000000',
                'relay_transaction_hash': '0x8800000000000000000000000000000000000000',
                'send_status': 'doing',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000040),
                'created_at': Decimal(int(1520150552.000040))
            },
            # status が fail
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x9900000000000000000000000000000000000000',
                'relay_transaction_hash': '0xaa00000000000000000000000000000000000000',
                'send_status': 'fail',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000050),
                'created_at': Decimal(int(1520150552.000050))
            },
            # 異なる日付
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x9900000000000000000000000000000000000000',
                'relay_transaction_hash': '0xaa00000000000000000000000000000000000000',
                'send_status': 'fail',
                'target_date': '2018-03-05',
                'sort_key': Decimal(1520150552000060),
                'created_at': Decimal(int(1520150552.000060))
            },
        ]
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        for i in items:
            token_send_table.put_item(Item=i)

        nonce = 5
        to_address = format(10, '064x')
        send_value = int(Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / Decimal(5))
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count, \
                patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed:
            # mock の初期化
            mock_get_allowance.return_value = '0x' + '0' * 64
            mock_get_transaction_count.return_value = format(nonce, '#x')
            mock_is_transaction_completed.return_value = True

            # テスト実施
            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': user_id,
                            'custom:private_eth_address': self.test_account.address,
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
            self.assertEqual(json.loads(response['body']), {'is_completed': True})

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), len(items) + 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(send_value),
                'approve_transaction': 'approve_transaction_hash',
                'relay_transaction_hash': 'relay_transaction_hash',
                'send_status': 'done',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000100),
                'created_at': Decimal(int(1520150552.000100))
            }
            sort_items = sorted(token_send_itmes, key=lambda x: x['sort_key'], reverse=True)
            self.assertEqual(expected_token_send, sort_items[0])

            # 各種メソッド呼び出し確認
            # mock_get_allowance
            self.assertEqual(mock_get_allowance.call_count, 1)
            args, _ = mock_get_allowance.call_args
            self.assertEqual(args[0], self.test_account.address)
            # get_transaction_count
            self.assertEqual(mock_get_transaction_count.call_count, 1)
            args, _ = mock_get_transaction_count.call_args
            self.assertEqual(args[0], self.test_account.address)
            # is_transaction_completed
            self.assertEqual(mock_is_transaction_completed.call_count, 1)
            args, _ = mock_is_transaction_completed.call_args
            self.assertEqual(args[0], 'relay_transaction_hash')

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['init_hash', 'approve_transaction_hash', 'relay_transaction_hash']))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ok_call_validate_methods(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        init_transaction = self.create_singed_approve_transaction(nonce, 0)
        approve_transaction = self.create_singed_approve_transaction(nonce + 1, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 2, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count, \
                patch('me_wallet_tip.UserUtil.verified_phone_and_email') as mock_verified_phone_and_email, \
                patch('me_wallet_tip.UserUtil.validate_private_eth_address') as mock_validate_private_eth_address, \
                patch('me_wallet_tip.PrivateChainUtil.validate_raw_transaction_signature') as mock_validate_signature, \
                patch('me_wallet_tip.PrivateChainUtil.validate_erc20_approve_data') \
                as mock_validate_erc20_approve_data, \
                patch('me_wallet_tip.PrivateChainUtil.validate_erc20_relay_data') as mock_validate_erc20_relay_data, \
                patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed:

            # mock の初期化
            mock_get_allowance.return_value = '0x1'
            mock_get_transaction_count.return_value = format(nonce, '#x')
            mock_is_transaction_completed.return_value = False

            # テスト実施
            event = {
                'body': {
                    'init_approve_signed_transaction': init_transaction,
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
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
            self.assertEqual(json.loads(response['body']), {'is_completed': False})

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(send_value),
                'approve_transaction': 'approve_transaction_hash',
                'relay_transaction_hash': 'relay_transaction_hash',
                'send_status': 'doing',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003))
            }
            self.assertEqual(expected_token_send, token_send_itmes[0])

            # 各種メソッド呼び出し確認
            # verified_phone_and_email
            args, _ = mock_verified_phone_and_email.call_args
            self.assertEqual(event, args[0])

            # validate_private_eth_address
            args, _ = mock_validate_private_eth_address.call_args
            self.assertEqual(self.dynamodb, args[0])
            self.assertEqual('user_01', args[1])

            # validate_raw_transaction_signature
            # init approve
            args, _ = mock_validate_signature.call_args_list[0]
            self.assertEqual(init_transaction, args[0])
            self.assertEqual(self.test_account.address, args[1])
            # approve
            args, _ = mock_validate_signature.call_args_list[1]
            self.assertEqual(approve_transaction, args[0])
            self.assertEqual(self.test_account.address, args[1])
            # relay
            args, _ = mock_validate_signature.call_args_list[2]
            self.assertEqual(relay_transaction, args[0])
            self.assertEqual(self.test_account.address, args[1])

            # mock_validate_erc20_approve_data
            # init approve
            args, _ = mock_validate_erc20_approve_data.call_args_list[0]
            init_data = PrivateChainUtil.get_data_from_raw_transaction(
                init_transaction,
                format(nonce, '#x')
            )
            self.assertEqual(init_data, args[0])
            # approve
            args, _ = mock_validate_erc20_approve_data.call_args_list[1]
            approve_data = PrivateChainUtil.get_data_from_raw_transaction(
                approve_transaction,
                format(nonce + 1, '#x')
            )
            self.assertEqual(approve_data, args[0])

            # mock_validate_erc20_relay_data
            # relay
            args, _ = mock_validate_erc20_relay_data.call_args_list[0]
            relay_data = PrivateChainUtil.get_data_from_raw_transaction(
                relay_transaction,
                format(nonce + 2, '#x')
            )
            self.assertEqual(relay_data, args[0])

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000100))
    @patch('time.time', MagicMock(return_value=1520150552.000100))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ng_over_limit(self):
        # 実行前データを作成
        user_id = 'user_01'
        items = [
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x1100000000000000000000000000000000000000',
                'relay_transaction_hash': '0x2200000000000000000000000000000000000000',
                'send_status': 'done',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000010),
                'created_at': Decimal(int(1520150552.000010))
            },
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x3300000000000000000000000000000000000000',
                'relay_transaction_hash': '0x4400000000000000000000000000000000000000',
                'send_status': 'done',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000020),
                'created_at': Decimal(int(1520150552.000020))
            },
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x5500000000000000000000000000000000000000',
                'relay_transaction_hash': '0x6600000000000000000000000000000000000000',
                'send_status': 'doing',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000030),
                'created_at': Decimal(int(1520150552.000030))
            },
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5,
                'approve_transaction': '0x7700000000000000000000000000000000000000',
                'relay_transaction_hash': '0x8800000000000000000000000000000000000000',
                'send_status': 'doing',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000040),
                'created_at': Decimal(int(1520150552.000040))
            },
            # 日次の制限にとの境界値テストを実施するため minimum 分を引いた値を設定。
            {
                'user_id': user_id,
                'send_value': Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / 5 - Decimal(
                    settings.parameters['token_send_value']['minimum']),
                'approve_transaction': '0x9900000000000000000000000000000000000000',
                'relay_transaction_hash': '0xaa00000000000000000000000000000000000000',
                'send_status': 'doing',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000050),
                'created_at': Decimal(int(1520150552.000050))
            }
        ]
        token_send_table = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        for i in items:
            token_send_table.put_item(Item=i)

        nonce = 5
        to_address = format(10, '064x')
        send_value = int(Decimal(os.environ['DAILY_LIMIT_TOKEN_SEND_VALUE']) / Decimal(5)) + 1
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count, \
                patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed:
            # mock の初期化
            mock_get_allowance.return_value = '0x' + '0' * 64
            mock_get_transaction_count.return_value = format(nonce, '#x')
            mock_is_transaction_completed.return_value = True

            # テスト実施
            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            result_items = token_send_table_name.scan()['Items']
            self.assertEqual(len(result_items), len(items))

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ng_not_exists_init_approve(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count:

            # mock の初期化
            mock_get_allowance.return_value = '0x1'
            mock_get_transaction_count.return_value = format(nonce, '#x')

            # テスト実施
            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(
                json.loads(response['body'])['message'],
                'Invalid parameter: init_approve_signed_transaction is invalid.'
            )

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ng_init_approve_value_not_zero(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        init_transaction = self.create_singed_approve_transaction(
            nonce,
            settings.parameters['token_send_value']['minimum']
        )
        approve_transaction = self.create_singed_approve_transaction(nonce + 1, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 2, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count:

            # mock の初期化
            mock_get_allowance.return_value = '0x1'
            mock_get_transaction_count.return_value = format(nonce, '#x')

            # テスト実施
            event = {
                'body': {
                    'init_approve_signed_transaction': init_transaction,
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(
                json.loads(response['body'])['message'],
                'Invalid parameter: Value of init_approve is invalid.'
            )

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ng_not_match_approve_value_and_relay_value(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value + 1)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count:

            # mock の初期化
            mock_get_allowance.return_value = '0x' + '0' * 64
            mock_get_transaction_count.return_value = format(nonce, '#x')

            # テスト実施
            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(
                json.loads(response['body'])['message'],
                'Invalid parameter: approve and relay values do not match.'
            )

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['approve_transaction_hash', 'relay_transaction_hash']))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ng_with_status_fail_at_SendTransactionError(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count, \
                patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed:
            # mock の初期化
            mock_get_allowance.return_value = '0x' + '0' * 64
            mock_get_transaction_count.return_value = format(nonce, '#x')
            mock_is_transaction_completed.side_effect = SendTransactionError()

            # テスト実施
            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 500)

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(send_value),
                'approve_transaction': 'approve_transaction_hash',
                'relay_transaction_hash': 'relay_transaction_hash',
                'send_status': 'fail',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003))
            }
            self.assertEqual(expected_token_send, token_send_itmes[0])

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['approve_transaction_hash', 'relay_transaction_hash']))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute', MagicMock())
    def test_main_ng_with_status_fail_at_ReceiptError(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value)

        with patch('private_chain_util.PrivateChainUtil.get_allowance') as mock_get_allowance, \
                patch('private_chain_util.PrivateChainUtil.get_transaction_count') as mock_get_transaction_count, \
                patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed:
            # mock の初期化
            mock_get_allowance.return_value = '0x' + '0' * 64
            mock_get_transaction_count.return_value = format(nonce, '#x')
            mock_is_transaction_completed.side_effect = ReceiptError()

            # テスト実施
            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 400)

            # DB 確認
            token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
            token_send_itmes = token_send_table_name.scan()['Items']
            self.assertEqual(len(token_send_itmes), 1)
            expected_token_send = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'send_value': Decimal(send_value),
                'approve_transaction': 'approve_transaction_hash',
                'relay_transaction_hash': 'relay_transaction_hash',
                'send_status': 'fail',
                'target_date': '2018-03-04',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003))
            }
            self.assertEqual(expected_token_send, token_send_itmes[0])

    def test_main_ng_invalid_pin_code(self):
        nonce = 5
        to_address = format(10, '064x')
        send_value = settings.parameters['token_send_value']['minimum']
        approve_transaction = self.create_singed_approve_transaction(nonce, send_value)
        relay_transaction = self.create_singed_relay_transaction(nonce + 1, to_address, send_value)

        with patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__verify_user_attribute') \
                as mock_verify_user_attribute, \
                patch('me_wallet_tip.PrivateChainUtil.validate_raw_transaction_signature'):

            event = {
                'body': {
                    'approve_signed_transaction': approve_transaction,
                    'relay_signed_transaction': relay_transaction,
                    'access_token': 'aaaaa',
                    'pin_code': '123456'
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

            # テスト対象実施
            mock_verify_user_attribute.side_effect = ClientError({'Error': {'Code': 'NotAuthorizedException'}}, '')
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter: Access token is invalid"}', response['body']))

            mock_verify_user_attribute.side_effect = ClientError({'Error': {'Code': 'CodeMismatchException'}}, '')
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter: Pin code is invalid"}', response['body']))

            mock_verify_user_attribute.side_effect = ClientError({'Error': {'Code': 'ExpiredCodeException'}}, '')
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter: Pin code is expired"}', response['body']))

            mock_verify_user_attribute.side_effect = ClientError({'Error': {'Code': 'LimitExceededException'}}, '')
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter: Verification limit is exceeded"}', response['body']))

            mock_verify_user_attribute.side_effect = ClientError({'Error': {'Code': 'Other'}}, '')
            response = MeWalletTokenSend(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 500)

    def create_singed_approve_transaction(self, nonce, value):
        method = '095ea7b3'
        approve_value = format(value, '064x')
        to_address = '0' * 24 + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        approve_data = method + to_address + approve_value
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 100000,
            'to': self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': approve_data,
            'chainId': 8995
        }
        return self.web3.eth.account.sign_transaction(transaction, self.test_account.key).rawTransaction.hex()

    def create_singed_relay_transaction(self, nonce, to_address, value):
        method = 'eeec0e24'
        relay_value = format(value, '064x')
        relay_data = method + to_address + relay_value
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 100000,
            'to': self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS']),
            'value': 0,
            'data': relay_data,
            'chainId': 8995
        }
        return self.web3.eth.account.sign_transaction(transaction, self.test_account.key).rawTransaction.hex()
