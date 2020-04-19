import os
import json
import settings
import re
from decimal import Decimal
from unittest import TestCase
from me_articles_purchase_create import MeArticlesPurchaseCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from web3 import Web3, HTTPProvider
from private_chain_util import PrivateChainUtil
from exceptions import SendTransactionError


class TestMeArticlesPurchaseCreate(TestCase):
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

        os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'] = "test"
        os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'] = "test"
        os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] = "test"

        self.article_info_table_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'article_user01',
                'status': 'public',
                'title': 'testid000001 title',
                'sort_key': 1520150272000000,
                'price': 1 * (10 ** 18)
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'article_user02',
                'status': 'public',
                'title': 'testid000002 title',
                'sort_key': 1520150272000000,
                'price': 10000 * (10 ** 18)
            },
            {
                'article_id': 'publicId0003',
                'user_id': 'article_user01',
                'status': 'public',
                'title': 'testid000001 title',
                'sort_key': 1520150272000000,
                'price': 100 * (10 ** 18)
            },
            {
                'article_id': 'publicId0004',
                'title': 'purchase001 title',
                'user_id': 'author001',
                'status': 'public',
                'sort_key': 1520150272000000,
                'price': 100 * (10 ** 18)
            },
            {
                'article_id': 'publicId0005',
                'title': 'purchase001 title',
                'user_id': 'author001',
                'status': 'public',
                'sort_key': 1520150272000000
            }
        ]

        self.article_history_table_items = [
            {
                'article_id': 'publicId0001',
                'title': 'sample_title1_history',
                'body': 'sample_body1_history',
                'created_at': 1520150270,
                'price': 1 * (10 ** 18)
            },
            {
                'article_id': 'publicId0001',
                'title': 'sample_title1_history',
                'body': 'sample_body1_history',
                'created_at': 1520150268,
                'price': 2 * (10 ** 18)
            },
            {
                'article_id': 'publicId0002',
                'title': 'sample_title2_history',
                'body': 'sample_body2_history',
                'created_at': 1520150268,
                'price': 10000 * (10 ** 18)
            },
            {
                'article_id': 'publicId0003',
                'title': 'sample_title2_history',
                'body': 'sample_body2_history',
                'created_at': 1520150270,
                'price': 100 * (10 ** 18)
            },
            {
                'article_id': 'publicId0004',
                'title': 'purchase001 title',
                'body': 'purchase001 body',
                'created_at': 1520150270,
                'price': 100 * (10 ** 18)
            }
        ]

        paid_article_items = [
            {
                'user_id': 'purchaseuser001',
                'article_user_id': 'author001',
                'article_title': 'purchase001 title',
                'price': 100 * (10 ** 18),
                'article_id': 'publicId0004',
                'status': 'fail',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }
        ]

        paid_status = [
            {
                'user_id': 'doublerequest001',
                'article_id': 'publicId0001',
                'status': 'doing',
                'created_at': 1520150552
            },
            {
                'user_id': 'purchaseuser001',
                'article_id': 'publicId0004',
                'status': 'fail',
                'created_at': 1520150552
            },
            {
                'user_id': 'doublerequest002',
                'article_id': 'publicId0001',
                'status': 'done',
                'created_at': 1520150552
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], self.article_info_table_items)
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_HISTORY_TABLE_NAME'],
                               self.article_history_table_items)
        TestsUtil.create_table(self.dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], paid_article_items)

        self.unread_notification_manager_table \
            = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'], [])

        self.notification_table \
            = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['NOTIFICATION_TABLE_NAME'], [])

        self.paid_status_table = TestsUtil.create_table(self.dynamodb, os.environ['PAID_STATUS_TABLE_NAME'], paid_status)

        user_configurations_items = [
            {
                'user_id': self.article_info_table_items[0]['user_id'],
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            },
            {
                'user_id': 'purchaseuser001',
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            },
            {
                'user_id': 'doublerequest001',
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            },
            {
                'user_id': 'doublerequest002',
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'], user_configurations_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeArticlesPurchaseCreate(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['purchase_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch("me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__get_randomhash",
           MagicMock(side_effect=[
               "d6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d",
               "0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57"
           ]))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000010))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_paid_status_fail(self):
        target_article = self.article_info_table_items[3]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "done"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': target_article['user_id'],
                'article_title': target_article['title'],
                'price': Decimal(target_article['price']),
                'article_id': target_article['article_id'],
                'status': 'done',
                'purchase_transaction': 'purchase_transaction_hash',
                'burn_transaction': 'burn_transaction_hash',
                'sort_key': Decimal(1520150552000010),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            expect_notifications = [
                {
                    'notification_id': 'd6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d',
                    'user_id': target_article['user_id'],
                    'acted_user_id': act_user_id,
                    'article_id': target_article['article_id'],
                    'article_user_id': target_article['user_id'],
                    'article_title': target_article['title'],
                    'sort_key': Decimal(1520150552000010),
                    'type': settings.ARTICLE_PURCHASED_TYPE,
                    'price': Decimal(100 * (10 ** 18)),
                    'created_at': Decimal(int(1520150552.000003))
                }, {
                    'notification_id': '0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57',
                    'user_id': act_user_id,
                    'acted_user_id': act_user_id,
                    'article_id': target_article['article_id'],
                    'article_user_id': target_article['user_id'],
                    'article_title': target_article['title'],
                    'sort_key': Decimal(1520150552000010),
                    'type': settings.ARTICLE_PURCHASE_TYPE,
                    'price': Decimal(100 * (10 ** 18)),
                    'created_at': Decimal(int(1520150552.000003))
                }
            ]

            # 記事購入に成功した場合は購入者と著者へ通知を行う
            actual_notifications = self.notification_table.scan()['Items']
            self.assertEqual(TestMeArticlesPurchaseCreate.__sorted_notifications(expect_notifications),
                             TestMeArticlesPurchaseCreate.__sorted_notifications(actual_notifications))
            # 失敗データが残っている状態で、新しい購入処理が成功すること
            self.assertEqual(paid_articles[0]['status'], 'fail')
            self.assertEqual(expected_purchase_article, paid_articles[1])
            self.assertEqual(len(self.unread_notification_manager_table.scan()['Items']), 2)
            # paid_statusがfailからdoneになること。paid_statusの件数が3件のままであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': act_user_id,
                'article_id': target_article['article_id']
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'done')
            self.assertEqual(paid_status.get('created_at'), 1520150552)
            self.assertEqual(len(paid_status_table.scan()['Items']), 3)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['purchase_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=False))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_transaction_unconfirmed(self):
        target_article = self.article_info_table_items[2]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "doing"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': target_article['user_id'],
                'article_title': target_article['title'],
                'price': Decimal(target_article['price']),
                'article_id': target_article['article_id'],
                'status': 'doing',
                'purchase_transaction': 'purchase_transaction_hash',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])
            self.assertEqual(len(self.unread_notification_manager_table.scan()['Items']), 0)
            # paid_statusが4件になること。生成したpaid_statusのstatusがdoingであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': act_user_id,
                'article_id': target_article['article_id']
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'doing')
            self.assertEqual(paid_status.get('created_at'), 1520150552)
            self.assertEqual(len(paid_status_table.scan()['Items']), 4)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['purchase_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_min_value(self):
        target_article = self.article_info_table_items[0]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "done"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': target_article['user_id'],
                'article_title': target_article['title'],
                'price': Decimal(target_article['price']),
                'article_id': target_article['article_id'],
                'status': 'done',
                'purchase_transaction': 'purchase_transaction_hash',
                'burn_transaction': 'burn_transaction_hash',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])
            # paid_statusが4件になること。生成したpaid_statusのstatusがdoneであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': act_user_id,
                'article_id': target_article['article_id']
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'done')
            self.assertEqual(paid_status.get('created_at'), 1520150552)
            self.assertEqual(len(paid_status_table.scan()['Items']), 4)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['purchase_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_max_value(self):
        target_article = self.article_info_table_items[1]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "done"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': target_article['user_id'],
                'article_title': target_article['title'],
                'price': Decimal(target_article['price']),
                'article_id': target_article['article_id'],
                'status': 'done',
                'purchase_transaction': 'purchase_transaction_hash',
                'burn_transaction': 'burn_transaction_hash',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150268)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ng_same_user(self):
        target_article = self.article_info_table_items[0]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = target_article['user_id']
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: Can not purchase own article"}')

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ng_invalid_purchase_value(self):
        target_article = self.article_info_table_items[0]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10)) - 1
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter: Price was changed', response['body']))
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ng_invalid_burn_value(self):
        target_article = self.article_info_table_items[0]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        # 10% ではなく、1%でしか burn 量を設定していない場合
        burn_value = int(test_purchase_value / Decimal(90))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter: burn_value is invalid', response['body']))
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ng_not_exists_private_eth_address(self):
        target_article = self.article_info_table_items[0]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_cognito_user_info') as mock_get_cognito_user_info:
            mock_get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'hoge',
                    'Value': 'fuga'
                }]
            }
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 404)
            self.assertEqual(response['body'], '{"message": "Record Not Found: private_eth_address"}')

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['purchase_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed',
           MagicMock(side_effect=SendTransactionError()))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_transaction_fail(self):
        target_article = self.article_info_table_items[1]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()

            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "fail"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': target_article['user_id'],
                'article_title': target_article['title'],
                'price': Decimal(target_article['price']),
                'article_id': target_article['article_id'],
                'status': 'fail',
                'purchase_transaction': 'purchase_transaction_hash',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150268)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])
            self.assertEqual(len(self.unread_notification_manager_table.scan()['Items']), 1)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['purchase_transaction_hash', Exception()]))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch("me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__get_randomhash",
           MagicMock(side_effect=[
               "d6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d",
               "0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57"
           ]))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000010))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_purchase_succeeded_but_failed_to_burn(self):
        target_article = self.article_info_table_items[3]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "done"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': target_article['user_id'],
                'article_title': target_article['title'],
                'price': Decimal(target_article['price']),
                'article_id': target_article['article_id'],
                'status': 'done',
                'purchase_transaction': 'purchase_transaction_hash',
                'sort_key': Decimal(1520150552000010),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            expect_notifications = [
                {
                    'notification_id': 'd6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d',
                    'user_id': target_article['user_id'],
                    'acted_user_id': act_user_id,
                    'article_id': target_article['article_id'],
                    'article_user_id': target_article['user_id'],
                    'article_title': target_article['title'],
                    'sort_key': Decimal(1520150552000010),
                    'type': settings.ARTICLE_PURCHASED_TYPE,
                    'price': Decimal(100 * (10 ** 18)),
                    'created_at': Decimal(int(1520150552.000003))
                }, {
                    'notification_id': '0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57',
                    'user_id': act_user_id,
                    'acted_user_id': act_user_id,
                    'article_id': target_article['article_id'],
                    'article_user_id': target_article['user_id'],
                    'article_title': target_article['title'],
                    'sort_key': Decimal(1520150552000010),
                    'type': settings.ARTICLE_PURCHASE_TYPE,
                    'price': Decimal(100 * (10 ** 18)),
                    'created_at': Decimal(int(1520150552.000003))
                }
            ]

            # 記事購入に成功した場合は購入者と著者へ通知を行う
            actual_notifications = self.notification_table.scan()['Items']
            self.assertEqual(TestMeArticlesPurchaseCreate.__sorted_notifications(expect_notifications),
                             TestMeArticlesPurchaseCreate.__sorted_notifications(actual_notifications))
            # 失敗データが残っている状態で、新しい購入処理が成功すること
            self.assertEqual(paid_articles[0]['status'], 'fail')
            self.assertEqual(expected_purchase_article, paid_articles[1])
            self.assertEqual(len(self.unread_notification_manager_table.scan()['Items']), 2)
            # paid_statusがfailからdoneになること。paid_statusの件数が3件のままであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': act_user_id,
                'article_id': target_article['article_id']
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'done')
            self.assertEqual(paid_status.get('created_at'), 1520150552)
            self.assertEqual(len(paid_status_table.scan()['Items']), 3)

    # 連続APIリクエストに対応するテスト(statusがdoingの場合)
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    def test_double_request_doing_ng(self):
        target_article = self.article_info_table_items[0]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'doublerequest001'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: You have already purchased"}')
            # paid statusの件数が3件から変更されていないこと。statusがdoingのままであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': 'doublerequest001',
                'article_id': 'publicId0001'
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'doing')
            self.assertEqual(paid_status.get('created_at'), 1520150552)
            self.assertEqual(len(paid_status_table.scan()['Items']), 3)

    # 連続APIリクエストに対応するテスト(statusがdoneの場合)
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    def test_double_request_done_ng(self):
        target_article = self.article_info_table_items[0]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'doublerequest002'
        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address:
            mock_get_private_eth_address.return_value = '0x' + to_address[24:]
            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: You have already purchased"}')
            # paid statusの件数が3件から変更されていないこと。statusがdoingのままであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': 'doublerequest001',
                'article_id': 'publicId0001'
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'doing')
            self.assertEqual(paid_status.get('created_at'), 1520150552)
            self.assertEqual(len(paid_status_table.scan()['Items']), 3)

    @patch('private_chain_util.PrivateChainUtil.send_raw_transaction', MagicMock(
        side_effect=['purchase_transaction_hash', 'burn_transaction_hash']))
    @patch('private_chain_util.PrivateChainUtil.get_transaction_count', MagicMock(return_value='0x5'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_call_validate_methods(self):
        target_article = self.article_info_table_items[1]
        test_purchase_value = int(target_article['price'] * Decimal(9) / Decimal(10))
        burn_value = int(test_purchase_value / Decimal(9))
        to_address = format(10, '064x')
        raw_transactions = self.create_singed_transactions(to_address, test_purchase_value, burn_value)
        act_user_id = 'purchaseuser001'

        with patch('me_articles_purchase_create.UserUtil.get_private_eth_address') as mock_get_private_eth_address, \
                patch('me_articles_purchase_create.UserUtil.verified_phone_and_email') \
                as mock_verified_phone_and_email, \
                patch('me_articles_purchase_create.UserUtil.validate_private_eth_address') \
                as mock_validate_private_eth_address, \
                patch('me_articles_purchase_create.PrivateChainUtil.validate_raw_transaction_signature') \
                as mock_validate_signature, \
                patch('me_articles_purchase_create.PrivateChainUtil.validate_erc20_transfer_data') \
                as mock_validate_erc20_transfer_data:

            mock_get_private_eth_address.return_value = '0x' + to_address[24:]

            event = {
                'body': {
                    'purchase_signed_transaction': raw_transactions['purchase'].rawTransaction.hex(),
                    'burn_signed_transaction': raw_transactions['burn'].rawTransaction.hex()
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': act_user_id,
                            'custom:private_eth_address': self.test_account.address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article['article_id']
                }
            }
            event['body'] = json.dumps(event['body'])
            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()

            self.assertEqual(response['statusCode'], 200)
            # verified_phone_and_email
            args, _ = mock_verified_phone_and_email.call_args
            self.assertEqual(event, args[0])
            # validate_private_eth_address
            args, _ = mock_validate_private_eth_address.call_args
            self.assertEqual(self.dynamodb, args[0])
            self.assertEqual(act_user_id, args[1])
            # validate_raw_transaction_signature
            args, _ = mock_validate_signature.call_args_list[0]
            self.assertEqual(raw_transactions['purchase'].rawTransaction.hex(), args[0])
            self.assertEqual(self.test_account.address, args[1])
            args, _ = mock_validate_signature.call_args_list[1]
            self.assertEqual(raw_transactions['burn'].rawTransaction.hex(), args[0])
            self.assertEqual(self.test_account.address, args[1])
            # validate_erc20_transfer_data
            args, _ = mock_validate_erc20_transfer_data.call_args_list[0]
            purchase_data = PrivateChainUtil.get_data_from_raw_transaction(
                raw_transactions['purchase'].rawTransaction.hex(),
                '0x5'
            )
            self.assertEqual(purchase_data, args[0])
            self.assertEqual('0x' + to_address[24:], args[1])
            args, _ = mock_validate_erc20_transfer_data.call_args_list[1]
            burn_data = PrivateChainUtil.get_data_from_raw_transaction(
                raw_transactions['burn'].rawTransaction.hex(),
                '0x6'
            )
            self.assertEqual(burn_data, args[0])
            self.assertEqual('0x' + os.environ['BURN_ADDRESS'], args[1])

            self.assertEqual(json.loads(response['body']), {"status": "done"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': target_article['user_id'],
                'article_title': target_article['title'],
                'price': Decimal(target_article['price']),
                'article_id': target_article['article_id'],
                'status': 'done',
                'purchase_transaction': 'purchase_transaction_hash',
                'burn_transaction': 'burn_transaction_hash',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150268)
            }
            self.assertEqual(expected_purchase_article, paid_articles[0])

    def test_validation_article_id_require(self):
        event = {
            'body': {
                'purchase_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_purchase_signed_transaction_require(self):
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
                'purchase_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_article_id_less_than_min(self):
        event = {
            'body': {
                'article_id': 'A' * 11,
                'purchase_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_article_id_greater_than_max(self):
        event = {
            'body': {
                'article_id': 'A' * 13,
                'purchase_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_article_id_use_invalid_char(self):
        event = {
            'body': {
                'article_id': 123456789012,
                'purchase_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_purchase_signed_transaction_use_invalid_char(self):
        event = {
            'body': {
                'article_id': 'A' * 12,
                'purchase_signed_transaction': '0xZZZAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_burn_signed_transaction_use_invalid_char(self):
        event = {
            'body': {
                'article_id': 'A' * 12,
                'purchase_signed_transaction': '0xAAAAAAAAAAAAAAAAAAAA',
                'burn_signed_transaction': '0xZZZBBBBBBBBBBBBBBBBBBBB'
            }
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def create_singed_transactions(self, to_address, test_purchase_value, burn_value):
        test_nonce = 5
        method = 'a9059cbb'
        purchase_value = format(test_purchase_value, '064x')
        purchase_data = method + to_address + purchase_value
        purchase_transaction = {
            'nonce': test_nonce,
            'gasPrice': 0,
            'gas': 0,
            'to': self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': purchase_data,
            'chainId': 8995
        }
        burn_address = format(0, '024x') + os.environ['BURN_ADDRESS']
        burn_value = format(burn_value, '064x')
        burn_data = method + burn_address + burn_value
        burn_transaction = {
            'nonce': test_nonce + 1,
            'gasPrice': 0,
            'gas': 0,
            'to': self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': burn_data,
            'chainId': 8995
        }
        return {
            'purchase': self.web3.eth.account.sign_transaction(purchase_transaction, self.test_account.key),
            'burn': self.web3.eth.account.sign_transaction(burn_transaction, self.test_account.key)
        }

    @staticmethod
    def __sorted_notifications(notifications):
        result = []
        for item in notifications:
            result.append(sorted(item.items(), key=lambda x: x[0]))

        return sorted(result)
