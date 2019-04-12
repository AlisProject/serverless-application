import os
import json
import settings
import re
from decimal import Decimal
from unittest import TestCase
from me_articles_purchase_create import MeArticlesPurchaseCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesPurchaseCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

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
                'title': 'testid000001 titile',
                'sort_key': 1520150272000000,
                'price': 1 * (10 ** 18)
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'article_user02',
                'status': 'public',
                'title': 'testid000002 titile',
                'sort_key': 1520150272000000,
                'price': 10000 * (10 ** 18)
            },
            {
                'article_id': 'publicId0003',
                'user_id': 'article_user01',
                'status': 'public',
                'title': 'testid000001 titile',
                'sort_key': 1520150272000000,
                'price': 100 * (10 ** 18)
            },
            {
                'article_id': 'publicId0004',
                'title': 'purchase001 titile',
                'user_id': 'author001',
                'status': 'public',
                'sort_key': 1520150272000000,
                'price': 100 * (10 ** 18)
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
                'title': 'purchase001 titile',
                'body': 'purchase001 body',
                'created_at': 1520150270,
                'price': 100 * (10 ** 18)
            }
        ]

        paid_article_items = [
            {
                'user_id': 'purchaseuser001',
                'article_user_id': 'author001',
                'article_title': 'purchase001 titile',
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
                'status': 'doing'
            },
            {
                'user_id': 'purchaseuser001',
                'article_id': 'publicId0004',
                'status': 'fail'
            },
            {
                'user_id': 'doublerequest002',
                'article_id': 'publicId0001',
                'status': 'done'
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

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeArticlesPurchaseCreate(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__polling_to_private_chain',
           MagicMock(return_value='done'))
    @patch("me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__get_randomhash",
           MagicMock(side_effect=[
               "d6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d",
               "0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57"
           ]))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000010))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            target_article_id = self.article_info_table_items[3]['article_id']
            price = str(100 * (10 ** 18))

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'purchaseuser001',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0004'
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
                'article_user_id': self.article_info_table_items[3]['user_id'],
                'article_title': 'purchase001 titile',
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'done',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': Decimal(1520150552000010),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            expect_notifications = [
                {
                    'notification_id': 'd6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d',
                    'user_id': 'author001',
                    'acted_user_id': 'purchaseuser001',
                    'article_id': 'publicId0004',
                    'article_user_id': 'author001',
                    'article_title': 'purchase001 titile',
                    'sort_key': Decimal(1520150552000010),
                    'type': settings.ARTICLE_PURCHASED_TYPE,
                    'price': Decimal(100 * (10 ** 18)),
                    'created_at': Decimal(int(1520150552.000003))
                }, {
                    'notification_id': '0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57',
                    'user_id': 'purchaseuser001',
                    'acted_user_id': 'purchaseuser001',
                    'article_id': 'publicId0004',
                    'article_user_id': 'author001',
                    'article_title': 'purchase001 titile',
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
                'user_id': 'purchaseuser001',
                'article_id': 'publicId0004'
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'done')
            self.assertEqual(len(paid_status_table.scan()['Items']), 3)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__polling_to_private_chain',
           MagicMock(return_value='doing'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_transaction_unconfirmed(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            target_article_id = self.article_info_table_items[2]['article_id']
            price = str(100 * (10 ** 18))

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0003'
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
                'article_user_id': self.article_info_table_items[2]['user_id'],
                'article_title': 'testid000001 titile',
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'doing',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])
            self.assertEqual(len(self.unread_notification_manager_table.scan()['Items']), 0)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__polling_to_private_chain',
           MagicMock(return_value='done'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000010))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_min_value(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            target_article_id = self.article_info_table_items[0]['article_id']
            price = str(1 * (10 ** 18))

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0001'
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
                'article_user_id': self.article_info_table_items[0]['user_id'],
                'article_title': 'testid000001 titile',
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'done',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': Decimal(1520150552000010),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])
            # paid_statusが4件になること。生成したpaid_statusのstatusがdoneであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': 'act_user_01',
                'article_id': 'publicId0001'
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'done')
            self.assertEqual(len(paid_status_table.scan()['Items']), 4)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__polling_to_private_chain',
           MagicMock(return_value='done'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_max_price(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            target_article_id = self.article_info_table_items[1]['article_id']
            price = str(settings.parameters['price']['maximum'])

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
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
                'article_title': 'testid000002 titile',
                'article_user_id': self.article_info_table_items[1]['user_id'],
                'price': Decimal(int(self.article_info_table_items[1]['price'])),
                'article_id': target_article_id,
                'status': 'done',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150268)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    @patch(
        'me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__check_transaction_confirmation',
        MagicMock(return_value='done'))
    def test_main_ng_same_user(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            price = str(1 * (10 ** 18))

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'article_user01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: Can not purchase own article"}')

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    @patch(
        'me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__check_transaction_confirmation',
        MagicMock(return_value='done'))
    def test_main_ng_not_exists_private_eth_address(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            price = str(1 * (10 ** 18))

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 404)
            self.assertEqual(response['body'], '{"message": "Record Not Found: private_eth_address"}')

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    def test_main_ng_less_than_min_value(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            price = str(1 * 10 ** 17)

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    def test_main_ng_minus_value(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            price = '-1'

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    def test_main_ng_bigger_than_max_value(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            price = str(settings.parameters['price']['maximum'] + 1)

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    def test_main_ng_not_number(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            price = 'aaaaaaaaaa'

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: Price must be integer"}')

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    def test_main_ng_price_is_decimal_value(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            price = str(1 * (10 ** 18) + 1 * (10 ** 17))

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': target_article_id
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: Decimal value is not allowed"}')

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__polling_to_private_chain',
           MagicMock(return_value='fail'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_transaction_fail(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            target_article_id = self.article_info_table_items[2]['article_id']
            price = str(100 * (10 ** 18))

            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'act_user_01',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0003'
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
                'article_user_id': self.article_info_table_items[2]['user_id'],
                'article_title': 'testid000001 titile',
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'fail',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])
            self.assertEqual(len(self.unread_notification_manager_table.scan()['Items']), 1)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__polling_to_private_chain',
           MagicMock(return_value='done'))
    @patch("me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__get_randomhash",
           MagicMock(side_effect=[
               "d6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d",
               "0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57"
           ]))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000010))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(side_effect=Exception()))
    def test_purchase_succeeded_but_failed_to_burn(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            price = str(100 * (10 ** 18))
            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'purchaseuser001',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0004'
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "done"})
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 2)

            expect_notifications = [
                {
                    'notification_id': 'd6f09fcaa6f409b7dde72957fdc17992d570e12ad23e8e968c29ab9aaea4df3d',
                    'user_id': 'author001',
                    'acted_user_id': 'purchaseuser001',
                    'article_id': 'publicId0004',
                    'article_user_id': 'author001',
                    'article_title': 'purchase001 titile',
                    'sort_key': Decimal(1520150552000010),
                    'type': settings.ARTICLE_PURCHASED_TYPE,
                    'price': Decimal(100 * (10 ** 18)),
                    'created_at': Decimal(int(1520150552.000003))
                }, {
                    'notification_id': '0e12ad23e8e968c29ab9aaea4df3dd6f09fcaa6f409b7dde72957fdc17992d57',
                    'user_id': 'purchaseuser001',
                    'acted_user_id': 'purchaseuser001',
                    'article_id': 'publicId0004',
                    'article_user_id': 'author001',
                    'article_title': 'purchase001 titile',
                    'sort_key': Decimal(1520150552000010),
                    'type': settings.ARTICLE_PURCHASE_TYPE,
                    'price': Decimal(100 * (10 ** 18)),
                    'created_at': Decimal(int(1520150552.000003))
                }
            ]

            # 購入者と著者へ購入通知が行われる
            actual_notifications = self.notification_table.scan()['Items']
            self.assertEqual(TestMeArticlesPurchaseCreate.__sorted_notifications(expect_notifications),
                             TestMeArticlesPurchaseCreate.__sorted_notifications(actual_notifications))

            self.assertEqual(len(self.unread_notification_manager_table.scan()['Items']), 2)

    @patch(
        'me_articles_purchase_create.MeArticlesPurchaseCreate.'
        '_MeArticlesPurchaseCreate__check_transaction_confirmation',
        MagicMock(return_value=json.dumps({
            "jsonrpc": "2.0",
            "result": None,
            "id": 1
        })))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    def test_polling_to_private_chain_tran_status_doing(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            price = str(100 * (10 ** 18))
            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'purchaseuser001',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0004'
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()

            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "doing"})

    @patch("me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__check_transaction_confirmation",
           MagicMock(return_value=json.dumps({
               "jsonrpc": "2.0",
               "error": {
                   "code": -32600,
                   "message": "Invalid request"
               },
               "id": None
           })))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    def test_polling_to_private_chain_tran_status_error(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            price = str(100 * (10 ** 18))
            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'purchaseuser001',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0004'
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()

            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "fail"})

    @patch(
        'me_articles_purchase_create.MeArticlesPurchaseCreate.'
        '_MeArticlesPurchaseCreate__check_transaction_confirmation',
        MagicMock(return_value=json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                'blockHash': '0xab698033e885b1ca0b4976063232df35db42eed57d9c12ad3937ab2bea33a55c',
                'blockNumber': '0x812ad',
                'contractAddress': None,
                'cumulativeGasUsed': '0x8ed2',
                'gasUsed': '0x8ed2',
                'logs': [
                    {
                        'address': '0x1383b25f9ba231e3a1a1e45c0b5689d778d44ad5',
                        'blockHash': '0xab698033e885b1ca0b4976063232df35db42eed57d9c12ad3937ab2bea33a55c',
                        'blockNumber': '0x812ad',
                        'data': '0x0000000000000000000000000000000000000000000000007ce66c50e2840000',
                        'logIndex': '0x0',
                        'topics': [
                            '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
                            '0x00000000000000000000000093f102758c661de802f7c50cc40daa03269e5d97',
                            '0x000000000000000000000000d29881fb9805aa4fddbec9c28c818bbac1951aee'
                        ],
                        'transactionHash': '0xa5999131185ec77a1e9f640a35149633c988b91990e4b18a506250dc2992d8fb',
                        'transactionIndex': '0x0',
                        'transactionLogIndex': '0x0',
                        'type': 'mined'
                    }
                ],
                'logsBloom': '0x00000000000000000000000000000002000000000000000000000000000000000000000000000400000000'
                             '0000000000000100000000000000000000000000000000000000000000000000080000000000000000000000'
                             '0000000000000000000000000000000000000000000000000000000000000000000000001000000000000000'
                             '0000000000000000000000000000000000000800000200010040000000000000000000000000000000400000'
                             '0000000000000000000000000000000000000000020000000000000000000000000000000000000000000000'
                             '00000000000000000000000000000000000000000000000000000000020000000000000000',
                'root': None, 'status': None,
                'transactionHash': '0xa5999131185ec77a1e9f640a35149633c988b91990e4b18a506250dc2992d8fb',
                'transactionIndex': '0x0'
            }})))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    def test_polling_to_private_chain_tran_status_done(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            price = str(100 * (10 ** 18))
            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'purchaseuser001',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0004'
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()

            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "done"})

    @patch(
        'me_articles_purchase_create.MeArticlesPurchaseCreate.'
        '_MeArticlesPurchaseCreate__check_transaction_confirmation',
        MagicMock(return_value=json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                'blockHash': '0xab698033e885b1ca0b4976063232df35db42eed57d9c12ad3937ab2bea33a55c',
                'blockNumber': '0x812ad',
                'contractAddress': None,
                'cumulativeGasUsed': '0x8ed2',
                'gasUsed': '0x8ed2',
                'logs': [
                    {
                        'address': '0x1383b25f9ba231e3a1a1e45c0b5689d778d44ad5',
                        'blockHash': '0xab698033e885b1ca0b4976063232df35db42eed57d9c12ad3937ab2bea33a55c',
                        'blockNumber': '0x812ad',
                        'data': '0x0000000000000000000000000000000000000000000000007ce66c50e2840000',
                        'logIndex': '0x0',
                        'topics': [
                            '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
                            '0x00000000000000000000000093f102758c661de802f7c50cc40daa03269e5d97',
                            '0x000000000000000000000000d29881fb9805aa4fddbec9c28c818bbac1951aee'
                        ],
                        'transactionHash': '0xa5999131185ec77a1e9f640a35149633c988b91990e4b18a506250dc2992d8fb',
                        'transactionIndex': '0x0',
                        'transactionLogIndex': '0x0',
                        # typeに予期せぬ値が来た場合で無限ループを再現
                        'type': 'hogehoge'
                    }
                ],
                'root': None, 'status': None,
                'transactionHash': '0xa5999131185ec77a1e9f640a35149633c988b91990e4b18a506250dc2992d8fb',
                'transactionIndex': '0x0'
            }})))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__create_purchase_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__burn_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000001'))
    def test_polling_to_private_chain_infinity_loop_break_ok(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            price = str(100 * (10 ** 18))
            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'purchaseuser001',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0004'
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()

            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), {"status": "doing"})

    # 連続APIリクエストに対応するテスト(statusがdoingの場合)
    def test_double_request_doing_ng(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            price = str(1 * (10 ** 18))
            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'doublerequest001',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0001'
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            # 400が返されること
            self.assertEqual(response['statusCode'], 400)
            # paid statusの件数が3件から変更されていないこと。statusがdoingのままであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': 'doublerequest001',
                'article_id': 'publicId0001'
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'doing')
            self.assertEqual(len(paid_status_table.scan()['Items']), 3)

    # 連続APIリクエストに対応するテスト(statusがdoneの場合)
    def test_double_request_done_ng(self):
        with patch('me_articles_purchase_create.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            price = str(1 * (10 ** 18))
            event = {
                'body': {
                    'price': price
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'doublerequest002',
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                },
                'pathParameters': {
                    'article_id': 'publicId0001'
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeArticlesPurchaseCreate(event, {}, self.dynamodb, cognito=None).main()
            # 400が返されること
            self.assertEqual(response['statusCode'], 400)
            # paid statusの件数が3件から変更されていないこと。statusがdoneのままであること
            paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
            paid_status = paid_status_table.get_item(Key={
                'user_id': 'doublerequest002',
                'article_id': 'publicId0001'
            }).get('Item')
            self.assertEqual(paid_status.get('status'), 'done')
            self.assertEqual(len(paid_status_table.scan()['Items']), 3)


    @staticmethod
    def __sorted_notifications(notifications):
        result = []
        for item in notifications:
            result.append(sorted(item.items(), key=lambda x: x[0]))

        return sorted(result)
