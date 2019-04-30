import os
import json
import re

from boto3.dynamodb.conditions import Key

import settings
from decimal import Decimal
from unittest import TestCase
from me_wallet_tip import MeWalletTip
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeWalletTip(TestCase):
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

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeWalletTip(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_min_value(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = str(settings.parameters['tip_value']['minimum'])

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
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
                'tip_value': Decimal(target_tip_value),
                'article_id': target_article_id,
                'article_title': self.article_info_table_items[0]['title'],
                'transaction': '0x0000000000000000000000000000000000000000',
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'past_data_exclusion_key': Decimal(1520150552000003),
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_max_value(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = str(settings.parameters['tip_value']['maximum'])

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
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
                'tip_value': Decimal(target_tip_value),
                'article_id': target_article_id,
                'article_title': self.article_info_table_items[0]['title'],
                'transaction': '0x0000000000000000000000000000000000000000',
                'uncompleted': Decimal(1),
                'sort_key': 1520150552000003,
                'past_data_exclusion_key': Decimal(1520150552000003),
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    def test_main_ng_same_user(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = str(1 * (10 ** 18))

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': self.article_info_table_items[0]['user_id'],
                            'custom:private_eth_address': '0x5d7743a4a6f21593ff6d3d81595f270123456789',
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

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    def test_main_ng_not_exists_private_eth_address(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = str(1 * (10 ** 18))

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
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
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 404)
            self.assertEqual(response['body'], '{"message": "Record Not Found: private_eth_address"}')

            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    def test_main_ng_less_than_min_value(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = '0'

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
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
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    def test_main_ng_minus_value(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = '-1'

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
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
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    def test_main_ng_greater_than_max_value(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = str(settings.parameters['tip_value']['maximum'] + 1)

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
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
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertIsNotNone(re.match('{"message": "Invalid parameter:', response['body']))

            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)

    def test_main_ng_not_number(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = 'aaaaaaaaaa'

            event = {
                'body': {
                    'article_id': target_article_id,
                    'tip_value': target_tip_value
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
                }
            }
            event['body'] = json.dumps(event['body'])

            response = MeWalletTip(event, {}, self.dynamodb, cognito=None).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(response['body'], '{"message": "Invalid parameter: Tip value must be numeric"}')

            tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])
            tips = tip_table.scan()['Items']
            self.assertEqual(len(tips), 0)
