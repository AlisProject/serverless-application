import os
import json
import settings
import re
import requests
from decimal import Decimal
from unittest import TestCase
from me_articles_purchase_create import MeArticlesPurchaseCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from time import sleep
from aws_requests_auth.aws_auth import AWSRequestsAuth


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
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], self.article_info_table_items)
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_HISTORY_TABLE_NAME'],
                               self.article_history_table_items)
        TestsUtil.create_table(self.dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], {})

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeArticlesPurchaseCreate(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value=json.dumps({
               'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
               'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
           })))
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
                    'article_id': target_article_id,
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
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': self.article_info_table_items[2]['user_id'],
                'article_title': 'testid000001 titile',
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'doing',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value=json.dumps({
               'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
               'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
           })))
    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__polling_to_private_chain',
           MagicMock(return_value='done'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
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
                    'article_id': target_article_id,
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
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': self.article_info_table_items[0]['user_id'],
                'article_title': 'testid000001 titile',
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'done',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value=json.dumps({
               'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
               'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
           })))
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
                    'article_id': target_article_id,
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
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

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

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value=json.dumps({
               'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
               'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
           })))
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
                    'article_id': target_article_id,
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
            self.assertEqual(len(paid_articles), 0)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value=json.dumps({
               'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
               'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
           })))
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
                    'article_id': target_article_id,
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
            self.assertEqual(len(paid_articles), 0)

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
                    'article_id': target_article_id,
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
            self.assertEqual(len(paid_articles), 0)

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
                    'article_id': target_article_id,
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
            self.assertEqual(len(paid_articles), 0)

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
                    'article_id': target_article_id,
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
            self.assertEqual(len(paid_articles), 0)

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
                    'article_id': target_article_id,
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
            self.assertEqual(len(paid_articles), 0)

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
                    'article_id': target_article_id,
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
            self.assertEqual(len(paid_articles), 0)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value=json.dumps({
               'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
               'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
           })))
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
                    'article_id': target_article_id,
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
            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 1)

            expected_purchase_article = {
                'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
                'article_user_id': self.article_info_table_items[2]['user_id'],
                'article_title': 'testid000001 titile',
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'fail',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])

    @patch(
        'test_me_articles_purchase_create.TestMeArticlesPurchaseCreate._TestMeArticlesPurchaseCreate__check_transaction_confirmation',
        MagicMock(return_value=json.dumps({
            "jsonrpc": "2.0",
            "result": None,
            "id": 1
        })))
    def test_polling_to_private_chain_tran_status_doing(self):
        transactions = {
            'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
            'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
        }
        status = 'doing'
        count = 2

        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')

        headers = {'content-type': 'application/json'}

        status = TestMeArticlesPurchaseCreate.__polling_to_private_chain(status, count, transactions, auth, headers)

        self.assertEqual(status, 'doing')

    @patch(
        'test_me_articles_purchase_create.TestMeArticlesPurchaseCreate._TestMeArticlesPurchaseCreate__check_transaction_confirmation',
        MagicMock(return_value=json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Invalid request"
            },
            "id": None
        })))
    def test_polling_to_private_chain_tran_status_error(self):
        transactions = {
            'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
            'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
        }
        status = 'doing'
        count = 0

        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')

        headers = {'content-type': 'application/json'}

        status = TestMeArticlesPurchaseCreate.__polling_to_private_chain(status, count, transactions, auth, headers)

        self.assertEqual(status, 'fail')

    @patch(
        'test_me_articles_purchase_create.TestMeArticlesPurchaseCreate._TestMeArticlesPurchaseCreate__check_transaction_confirmation',
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
                'logsBloom': '0x00000000000000000000000000000002000000000000000000000000000000000000000000000400000000000000000000010000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000800000200010040000000000000000000000000000000400000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020000000000000000',
                'root': None, 'status': None,
                'transactionHash': '0xa5999131185ec77a1e9f640a35149633c988b91990e4b18a506250dc2992d8fb',
                'transactionIndex': '0x0'
            }})))
    def test_polling_to_private_chain_tran_status_done(self):
        transactions = {
            'purchase_transaction_hash': '0x0000000000000000000000000000000000000000',
            'burn_transaction_hash': '0x0000000000000000000000000000000000000001'
        }
        status = 'doing'
        count = 1

        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')

        headers = {'content-type': 'application/json'}

        status = TestMeArticlesPurchaseCreate.__polling_to_private_chain(status, count, transactions, auth, headers)

        self.assertEqual(status, 'done')

    @staticmethod
    def __polling_to_private_chain(status, count, transactions, auth, headers):
        # 最大3回トランザクション詳細を問い合わせる
        while count < 3 and status == 'doing':
            # 1秒待機
            sleep(1)
            # check whether transaction is completed
            transaction_status = TestMeArticlesPurchaseCreate.__check_transaction_confirmation(transactions, auth,
                                                                                               headers)
            result = json.loads(transaction_status).get('result')
            # exists error
            if json.loads(transaction_status).get('error'):
                return 'fail'
            if result is None or result['logs'] == 0:
                count += 1
                continue
            if result['logs'][0].get('type') == 'mined':
                return 'done'
        return 'doing'

    @staticmethod
    def __check_transaction_confirmation(transactions, auth, headers):
        receipt_payload = json.dumps(
            {
                'transaction_hash': json.loads(transactions).get('purchase_transaction_hash')
            }
        )
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/transaction/receipt', auth=auth, headers=headers, data=receipt_payload)
        return response.text
