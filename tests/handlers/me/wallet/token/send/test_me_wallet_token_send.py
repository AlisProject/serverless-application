import os
import json
import re
import settings
from decimal import Decimal
from unittest import TestCase
from me_wallet_token_send import MeWalletTokenSend
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesCommentsCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

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

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_min_value(self):
        target_token_send_value = str(settings.parameters['token_send_value']['minimum'])
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
        self.assertEqual(response['statusCode'], 200)
        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        token_send_itmes = token_send_table_name.scan()['Items']
        self.assertEqual(len(token_send_itmes), 1)

        expected_token_send = {
            'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
            'send_value': Decimal(target_token_send_value),
            'approve_transaction': '0x0000000000000000000000000000000000000000',
            'withdraw_transaction_hash': '0x1000000000000000000000000000000000000000',
            'uncompleted': Decimal(1),
            'sort_key': Decimal(1520150552000003),
            'created_at': Decimal(int(1520150552.000003))
        }

        self.assertEqual(expected_token_send, token_send_itmes[0])

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_max_value(self):
        target_token_send_value = str(settings.parameters['token_send_value']['maximum'])
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
        self.assertEqual(response['statusCode'], 200)
        token_send_table_name = self.dynamodb.Table(os.environ['TOKEN_SEND_TABLE_NAME'])
        token_send_itmes = token_send_table_name.scan()['Items']
        self.assertEqual(len(token_send_itmes), 1)

        expected_token_send = {
            'user_id': event['requestContext']['authorizer']['claims']['cognito:username'],
            'send_value': Decimal(target_token_send_value),
            'approve_transaction': '0x0000000000000000000000000000000000000000',
            'withdraw_transaction_hash': '0x1000000000000000000000000000000000000000',
            'uncompleted': Decimal(1),
            'sort_key': Decimal(1520150552000003),
            'created_at': Decimal(int(1520150552.000003))
        }

        self.assertEqual(expected_token_send, token_send_itmes[0])

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
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

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
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

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
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

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
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

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
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

    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__approve',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_token_send.MeWalletTokenSend._MeWalletTokenSend__withdraw',
           MagicMock(return_value='0x1000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
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
