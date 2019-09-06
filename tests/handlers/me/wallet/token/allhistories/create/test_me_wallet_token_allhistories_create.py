import os
import boto3
from unittest import TestCase
from me_wallet_token_allhistories_create import MeWalletTokenAllhistoriesCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from hexbytes import HexBytes

class TestMeWalletTokenAllHistoriesCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()
    s3 = boto3.resource('s3', endpoint_url='http://localhost:4572/')

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_aws_auth_to_env()
        TestsUtil.set_all_private_chain_valuables_to_env()
        TestsUtil.set_all_s3_buckets_name_to_env()
        TestsUtil.create_all_s3_buckets(cls.s3)
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        cls.notification_items = [
            {
                'notification_id': 'like-test01-test_article01',
                'user_id': 'test01',
                'sort_key': 1520150272000005,
                'article_id': 'test_article01',
                'article_title': 'test_title01',
                'type': 'like',
                'liked_count': 5,
                'created_at': 1520150272
            }
        ]
        cls.unread_notification_manager_items = [
            {
                'user_id': 'user_01',
                'unread': False
            },
            {
                'user_id': 'user_02',
                'unread': False
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['NOTIFICATION_TABLE_NAME'], cls.notification_items)
        TestsUtil.create_table(cls.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'], cls.unread_notification_manager_items)

    def assert_bad_request(self, params):
        target_function = MeWalletTokenAllhistoriesCreate(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('web3.eth.Eth.getBlock',
           MagicMock(return_value={'timestamp': 1546268400}))
    @patch('me_wallet_token_allhistories_create.MeWalletTokenAllhistoriesCreate._MeWalletTokenAllhistoriesCreate__get_randomhash',
           MagicMock(return_value='notification_id_randomhash'))
    def test_main_ok(self):
        with patch('web3.eth.Eth.filter') as web3_eth_filter_mock, patch('me_wallet_token_allhistories_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            web3_eth_filter_mock.return_value = PrivateChainEthFilterFakeResponse()

            event = {
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': '0x1111111111111111111111111111111111111111',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
             }

            unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
            unread_notification_manager_before = unread_notification_manager_table.get_item(
                Key={'user_id': 'user_01'}
            ).get('Item')
            self.assertEqual(unread_notification_manager_before['unread'], False)

            notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
            notification_before = notification_table.scan()['Items']

            response = MeWalletTokenAllhistoriesCreate(event, {}, dynamodb=self.dynamodb, s3=self.s3).main()
            self.assertEqual(response['statusCode'], 200)

            notification_after = notification_table.scan()['Items']

            unread_notification_manager_after = unread_notification_manager_table.get_item(
                Key={'user_id': 'user_01'}
            ).get('Item')

            notification_type = notification_table.get_item(
                Key={'notification_id': 'notification_id_randomhash'}
            ).get('Item').get('type')

            self.assertEqual(len(notification_after), len(notification_before) + 1)
            self.assertEqual(unread_notification_manager_after['unread'], True)
            self.assertEqual(notification_type, 'csvdownload')

    @patch('web3.eth.Eth.getBlock',
           MagicMock(return_value={'timestamp': 1546268400}))
    def test_ok_with_several_data(self):
        with patch('web3.eth.Eth.filter') as web3_eth_filter_with_several_data_mock, patch('me_wallet_token_allhistories_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            web3_eth_filter_with_several_data_mock.return_value = PrivateChainEthFilterFakeResponseWithSeveralData()

            event = {
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': '0x1111111111111111111111111111111111111111',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
             }

            response = MeWalletTokenAllhistoriesCreate(event, {}, dynamodb=self.dynamodb, s3=self.s3).main()
            self.assertEqual(response['statusCode'], 200)

    @patch('web3.eth.Eth.getBlock',
           MagicMock(return_value={'timestamp': 1546268400}))
    def test_ok_with_no_data(self):
        with patch('web3.eth.Eth.filter') as web3_eth_filter_with_no_data_mock, patch('me_wallet_token_allhistories_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            web3_eth_filter_with_no_data_mock.return_value = PrivateChainEthFilterFakeResponseWithNoData()

            event = {
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': '0x1111111111111111111111111111111111111111',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
             }

            response = MeWalletTokenAllhistoriesCreate(event, {}, dynamodb=self.dynamodb, s3=self.s3).main()
            self.assertEqual(response['statusCode'], 404)

    def test_add_type_ok(self):
        with patch('me_wallet_token_allhistories_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            event = {
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': '0x1111111111111111111111111111111111111111',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
             }

            user_eoa = event['requestContext']['authorizer']['claims']['custom:private_eth_address']
            MeWalletTokenAllhistoriesCreate.eoa = user_eoa
            alis_bridge_contract_address = '0x20326c2C26C5F5D314316131d815eb92940e761A'

            response = MeWalletTokenAllhistoriesCreate(event, {}, self.dynamodb).add_type(user_eoa, alis_bridge_contract_address)
            self.assertEqual(response, 'withdraw')
            response = MeWalletTokenAllhistoriesCreate(event, {}, self.dynamodb).add_type(user_eoa, '0x0123456789012345678901234567890123456789')
            self.assertEqual(response, 'give')
            response = MeWalletTokenAllhistoriesCreate(event, {}, self.dynamodb).add_type(user_eoa, '0x0000000000000000000000000000000000000000')
            self.assertEqual(response, 'burn')
            response = MeWalletTokenAllhistoriesCreate(event, {}, self.dynamodb).add_type(alis_bridge_contract_address, user_eoa)
            self.assertEqual(response, 'deposit')
            response = MeWalletTokenAllhistoriesCreate(event, {}, self.dynamodb).add_type('---', user_eoa)
            self.assertEqual(response, 'get by like')
            response = MeWalletTokenAllhistoriesCreate(event, {}, self.dynamodb).add_type('0x0123456789012345678901234567890123456789', user_eoa)
            self.assertEqual(response, 'get from an user')
            response = MeWalletTokenAllhistoriesCreate(event, {}, self.dynamodb).add_type('---', None)
            self.assertEqual(response, 'unknown')

class PrivateChainEthFilterFakeResponse:
    def __init__(self):
        self.eth_filter_mock_value = MagicMock()
        self.eth_filter_mock_value.side_effect = [
                [{'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                 'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bba7'),
                 'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                 'logIndex': 0,
                 'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                            HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111'),
                            HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')],
                 'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4879456'),
                 'transactionIndex': 0,
                 'transactionLogIndex': '0x0',
                 'type': 'mined'}],
                [{'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                 'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bba8'),
                 'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                 'logIndex': 0,
                 'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                            HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000'),
                            HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111')],
                 'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4879457'),
                 'transactionIndex': 0,
                 'transactionLogIndex': '0x0',
                 'type': 'mined'}],
                [{'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                 'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bba9'),
                 'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                 'logIndex': 0,
                 'topics': [HexBytes('0x0f6798a560793a54c3bcfe86a93cde1e73087d944c0ea20544137d4121396885'),
                            HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111'),
                            HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')],
                 'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4879458'),
                 'transactionIndex': 0,
                 'transactionLogIndex': '0x0',
                 'type': 'mined'}],
            ]
    def get_all_entries(self):
        return self.eth_filter_mock_value()

class PrivateChainEthFilterFakeResponseWithSeveralData:
    def __init__(self):
        self.eth_filter_mock_value = MagicMock()
        self.eth_filter_mock_value.side_effect = [
                [{'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                 'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bba7'),
                 'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                 'logIndex': 0,
                 'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                            HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111'),
                            HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')],
                 'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4879456'),
                 'transactionIndex': 0,
                 'transactionLogIndex': '0x0',
                 'type': 'mined'},
                 {'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                 'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bba6'),
                 'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                 'logIndex': 0,
                 'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                            HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111'),
                            HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')],
                 'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4879446'),
                 'transactionIndex': 0,
                 'transactionLogIndex': '0x0',
                 'type': 'mined'}],
                [{'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                 'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bba8'),
                 'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                 'logIndex': 0,
                 'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                            HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000'),
                            HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111')],
                 'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4879457'),
                 'transactionIndex': 0,
                 'transactionLogIndex': '0x0',
                 'type': 'mined'},
                 {'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                  'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bbc8'),
                  'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                  'logIndex': 0,
                  'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                             HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000'),
                             HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111')],
                  'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4873457'),
                  'transactionIndex': 0,
                  'transactionLogIndex': '0x0',
                  'type': 'mined'}],
                [{'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                 'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271725c99bb5c690bba9'),
                 'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                 'logIndex': 0,
                 'topics': [HexBytes('0x0f6798a560793a54c3bcfe86a93cde1e73087d944c0ea20544137d4121396885'),
                            HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111'),
                            HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')],
                 'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4879458'),
                 'transactionIndex': 0,
                 'transactionLogIndex': '0x0',
                 'type': 'mined'},
                 {'address': '0x1383B25f9ba231e3a1a1E45c0b5689d778D44AD5',
                  'blockHash': HexBytes('0xf32e073349e4ca49c5e193b161ea1b9ba7dc9c2a9bf1271721c99bb5c690bba9'),
                  'blockNumber': 836877, 'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                  'logIndex': 0,
                  'topics': [HexBytes('0x0f6798a560793a54c3bcfe86a93cde1e73087d944c0ea20544137d4121396885'),
                             HexBytes('0x0000000000000000000000001111111111111111111111111111111111111111'),
                             HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')],
                  'transactionHash': HexBytes('0xf45f335a0bb17d112e870f98218ebd5159e5d7ab9f1739677d7c0b3df4829458'),
                  'transactionIndex': 0,
                  'transactionLogIndex': '0x0',
                  'type': 'mined'}],
            ]
    def get_all_entries(self):
        return self.eth_filter_mock_value()

class PrivateChainEthFilterFakeResponseWithNoData:
    def get_all_entries(self):
        value = {}
        return value
