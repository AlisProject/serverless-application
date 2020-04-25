import os
import json
import re

import settings
from decimal import Decimal
from unittest import TestCase
from me_wallet_tip import MeWalletTip
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from web3 import Web3, HTTPProvider
from private_chain_util import PrivateChainUtil


class TestMeWalletTip(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls) -> None:
        TestsUtil.set_aws_auth_to_env()
        TestsUtil.set_all_private_chain_valuables_to_env()
        cls.web3 = Web3(HTTPProvider('http://localhost:8584'))
        cls.test_account = cls.web3.eth.account.create()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        TestsUtil.set_aws_auth_to_env()

        self.article_info_table_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'article_user01',
                'status': 'public',
                'title': 'testid000001 titile',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'article_user02',
                'status': 'public',
                'title': 'testid000002 titile',
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], self.article_info_table_items)
        TestsUtil.create_table(self.dynamodb, os.environ['TIP_TABLE_NAME'], {})

        user_configurations_items = [
            {
                'user_id': self.article_info_table_items[0]['user_id'],
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            },
            {
                'user_id': 'act_user_01',
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'], user_configurations_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, event):
        response = MeWalletTip(event, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['tip_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.get_balance', MagicMock(return_value=format(10 ** 30, '#x')))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_min_value(self):
        test_tip_value = 10
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 1)

            expected_tip = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'to_user_id': self.article_info_table_items[0]['user_id'],
                'tip_value': Decimal(test_tip_value),
                'article_id': target_article_id,
                'article_title': self.article_info_table_items[0]['title'],
                'transaction': 'tip_transaction_hash',
                'burn_transaction': 'burn_transaction_hash',
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['tip_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.get_balance', MagicMock(return_value=format(10 ** 30, '#x')))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_max_value(self):
        test_tip_value = settings.parameters['tip_value']['maximum']
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 1)

            expected_tip = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'to_user_id': self.article_info_table_items[0]['user_id'],
                'tip_value': Decimal(test_tip_value),
                'article_id': target_article_id,
                'article_title': self.article_info_table_items[0]['title'],
                'transaction': 'tip_transaction_hash',
                'burn_transaction': 'burn_transaction_hash',
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.get_balance', MagicMock(return_value=format(10 ** 30, '#x')))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=False))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_with_wrong_transaction_status(self):
        test_tip_value = 10
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address,\
                patch('private_chain_util.PrivateChainUtil.send_raw_transaction') as mock_send_raw_transaction:

            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            mock_send_raw_transaction.return_value = 'tip_transaction_hash'
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 1)

            expected_tip = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'to_user_id': self.article_info_table_items[0]['user_id'],
                'tip_value': Decimal(test_tip_value),
                'article_id': target_article_id,
                'article_title': self.article_info_table_items[0]['title'],
                'transaction': 'tip_transaction_hash',
                'burn_transaction': None,
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])
            # tip_transaction のみ実行されていること
            self.assertEqual(mock_send_raw_transaction.call_count, 1)

    # 109 しかtokenを持ってないユーザーで 110 tokenを投げ銭する
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.get_balance', MagicMock(return_value=format(109, '#x')))
    def test_main_ng_with_not_burnable_user(self):
        test_tip_value = 100
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(json.loads(response['body'])['message'], 'Invalid parameter: Required at least 110 token')
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['tip_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.get_balance', MagicMock(return_value=format(10 ** 30, '#x')))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(side_effect=Exception()))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_with_exception_in_is_transaction_completed(self):
        test_tip_value = 10
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 1)

            expected_tip = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'to_user_id': self.article_info_table_items[0]['user_id'],
                'tip_value': Decimal(test_tip_value),
                'article_id': target_article_id,
                'article_title': self.article_info_table_items[0]['title'],
                'transaction': 'tip_transaction_hash',
                'burn_transaction': None,
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.get_balance', MagicMock(return_value=format(10 ** 30, '#x')))
    def test_main_ng_same_user(self):
        test_tip_value = 100
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': self.article_info_table_items[0]['user_id'],
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: Can not tip to myself"}')

            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    def test_main_ng_not_exists_private_eth_address(self):
        test_tip_value = 100
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_cognito_user_info') as mock_get_cognito_user_info:
            mock_get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'hoge',
                    'Value': 'piyo'
                }]
            }
            target_article_id = self.article_info_table_items[0]['article_id']
            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 404)
            self.assertEqual(response['body'], '{"message": "Record Not Found: private_eth_address"}')

            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    def test_main_ng_less_than_min_value(self):
        test_tip_value = 0
        to_address = format(10, '064x')
        burn_value = 0
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(
                re.match('{"message": "Invalid parameter: 0 is less than the minimum of 1', response['body']))
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    def test_main_ng_greater_than_max_value(self):
        test_tip_value = settings.parameters['tip_value']['maximum'] + 1
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(
                re.match('{"message": "Invalid parameter: 1000000000000000000000001 is greater than the maximum of '
                         '1000000000000000000000000', response['body']))
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    def test_main_ng_invalid_burn_value(self):
        test_tip_value = 100
        to_address = format(10, '064x')
        # 10% ではなく、1%でしか burn 量を設定していない場合
        burn_value = int(test_tip_value / Decimal(100))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter: burn_value is invalid', response['body']))
            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['tip_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.get_balance', MagicMock(return_value=format(10 ** 30, '#x')))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_call_validate_methods(self):
        test_tip_value = 10
        to_address = format(10, '064x')
        burn_value = int(test_tip_value / Decimal(10))
        raw_transactions = self.create_singed_transactions(to_address, test_tip_value, burn_value)

        with patch('me_wallet_tip.UserUtil.get_private_eth_address') as mock_get_private_eth_address, \
                patch('me_wallet_tip.UserUtil.verified_phone_and_email') as mock_verified_phone_and_email, \
                patch('me_wallet_tip.UserUtil.validate_private_eth_address') as mock_validate_private_eth_address, \
                patch('me_wallet_tip.PrivateChainUtil.validate_raw_transaction_signature') as mock_validate_signature, \
                patch('me_wallet_tip.PrivateChainUtil.validate_erc20_transfer_data') \
                as mock_validate_erc20_transfer_data:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            target_article_id = self.article_info_table_items[0]['article_id']

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_signed_transaction': raw_transactions['tip'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            # verified_phone_and_email
            args, _ = mock_verified_phone_and_email.call_args
            self.assertEqual(event, args[0])
            # validate_private_eth_address
            args, _ = mock_validate_private_eth_address.call_args
            self.assertEqual(self.dynamodb, args[0])
            self.assertEqual('act_user_01', args[1])
            # validate_raw_transaction_signature
            args, _ = mock_validate_signature.call_args_list[0]
            self.assertEqual(raw_transactions['tip'].rawTransaction.hex(), args[0])
            self.assertEqual(self.test_account.address, args[1])
            args, _ = mock_validate_signature.call_args_list[1]
            self.assertEqual(raw_transactions['burn'].rawTransaction.hex(), args[0])
            self.assertEqual(self.test_account.address, args[1])
            # validate_erc20_transfer_data
            args, _ = mock_validate_erc20_transfer_data.call_args_list[0]
            tip_data = PrivateChainUtil.get_data_from_raw_transaction(
                raw_transactions['tip'].rawTransaction.hex(),
                '0x5'
            )
            self.assertEqual(tip_data, args[0])
            self.assertEqual('0x' + to_address[24:], args[1])
            args, _ = mock_validate_erc20_transfer_data.call_args_list[1]
            burn_data = PrivateChainUtil.get_data_from_raw_transaction(
                raw_transactions['burn'].rawTransaction.hex(),
                '0x6'
            )
            self.assertEqual(burn_data, args[0])
            self.assertEqual('0x' + os.environ['BURN_ADDRESS'], args[1])

    def test_validation_article_id_require(self):
        event = {
            'body': {
                'tip_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_tip_signed_transaction_require(self):
        event = {
            'body': {
                'article_id': 'A' * 12,
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_burn_signed_transaction_require(self):
        event = {
            'body': {
                'article_id': 'A' * 12,
                'tip_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_article_id_less_than_min(self):
        event = {
            'body': {
                'article_id': 'A' * 11,
                'tip_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_article_id_greater_than_max(self):
        event = {
            'body': {
                'article_id': 'A' * 13,
                'tip_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_article_id_use_invalid_char(self):
        event = {
            'body': {
                'article_id': 123456789012,
                'tip_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_tip_signed_transaction_use_invalid_char(self):
        event = {
            'body': {
                'article_id': 'A' * 12,
                'tip_signed_transaction': '0xZZZAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_burn_signed_transaction_use_invalid_char(self):
        event = {
            'body': {
                'article_id': 'A' * 12,
                'tip_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xZZZBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def create_singed_transactions(self, to_address, test_tip_value, burn_value):
        test_nonce = 5
        method = 'a9059cbb'
        tip_value = format(test_tip_value, '064x')
        tip_data = method + to_address + tip_value
        tip_transaction = {
            'nonce': test_nonce,
            'gasPrice': 0,
            'gas': 100000,
            'to': self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': tip_data,
            'chainId': 8995
        }
        burn_address = format(0, '024x') + os.environ['BURN_ADDRESS']
        burn_value = format(burn_value, '064x')
        burn_data = method + burn_address + burn_value
        burn_transaction = {
            'nonce': test_nonce + 1,
            'gasPrice': 0,
            'gas': 100000,
            'to': self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': burn_data,
            'chainId': 8995
        }
        return {
            'tip': self.web3.eth.account.sign_transaction(tip_transaction, self.test_account.key),
            'burn': self.web3.eth.account.sign_transaction(burn_transaction, self.test_account.key)
        }
