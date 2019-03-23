import os
import json
import settings
import time
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
                'price': 2 * (10 ** 18)
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
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], self.article_info_table_items)
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_HISTORY_TABLE_NAME'], self.article_history_table_items)
        TestsUtil.create_table(self.dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], {})

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeArticlesPurchaseCreate(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
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
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'doing',
                'transaction': '0x0000000000000000000000000000000000000000',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
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

            target_article_id = self.article_info_table_items[0]['article_id']
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
                'article_user_id': self.article_info_table_items[0]['user_id'],
                'price': Decimal(price),
                'article_id': target_article_id,
                'status': 'doing',
                'transaction': '0x0000000000000000000000000000000000000000',
                'sort_key': Decimal(1520150552000003),
                'created_at': Decimal(int(1520150552.000003)),
                'history_created_at': Decimal(1520150270)
            }

            self.assertEqual(expected_purchase_article, paid_articles[0])

    @patch('me_articles_purchase_create.MeArticlesPurchaseCreate._MeArticlesPurchaseCreate__purchase_article',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
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
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
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
            self.assertEqual(response['body'], '{"message": "Invalid parameter: Price must be numeric"}')

            paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
            paid_articles = paid_articles_table.scan()['Items']
            self.assertEqual(len(paid_articles), 0)
