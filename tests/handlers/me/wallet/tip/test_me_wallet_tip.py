import os
import json
import re

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

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        target_function = MeWalletTip(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=True))
    @patch('private_chain_util.PrivateChainUtil.send_transaction', MagicMock(return_value=1))
    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__burn_transaction', MagicMock(return_value='burn_transaction_hash'))
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
                'burn_transaction': 'burn_transaction_hash',
                'uncompleted': Decimal(1),
                'sort_key': Decimal(1520150552000003),
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('private_chain_util.PrivateChainUtil.send_transaction', MagicMock(
        return_value=settings.parameters['tip_value']['maximum'] + settings.parameters['tip_value']['maximum'] / Decimal(10)))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_max_value(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock, \
             patch('private_chain_util.PrivateChainUtil.is_transaction_completed') as mock_is_transaction_completed, \
             patch('me_wallet_tip.MeWalletTip._MeWalletTip__burn_transaction') as mock_burn_transaction:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            mock_is_transaction_completed.return_value = True
            mock_burn_transaction.return_value = 'burn_transaction_hash'

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
            self.assertEqual(mock_is_transaction_completed.call_count, 1)
            self.assertEqual(mock_burn_transaction.call_count, 1)
            args, kwargs = mock_burn_transaction.call_args
            self.assertEqual(args[0], int(settings.parameters['tip_value']['maximum'] / Decimal(10)))
            self.assertEqual(args[1], '0x5d7743a4a6f21593ff6d3d81595f270123456789')

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
                'burn_transaction': 'burn_transaction_hash',
                'uncompleted': Decimal(1),
                'sort_key': 1520150552000003,
                'target_date': '2018-03-04',
                'created_at': Decimal(int(1520150552.000003))
            }

            self.assertEqual(expected_tip, tips[0])

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__is_burnable_user', MagicMock(return_value=True))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(return_value=False))
    def test_main_ok_with_wrong_transaction_status(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock, \
             patch('me_wallet_tip.MeWalletTip._MeWalletTip__burn_transaction') as mock_burn_transaction:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            mock_burn_transaction.return_value = 'burn_transaction_hash'

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

            self.assertEqual(mock_burn_transaction.call_count, 0)

    # 109 しかtokenを持ってないユーザーで 110 tokenを投げ銭する
    @patch('private_chain_util.PrivateChainUtil.send_transaction', MagicMock(return_value=109))
    def test_main_ng_with_not_burnable_user(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock, \
             patch('me_wallet_tip.MeWalletTip._MeWalletTip__burn_transaction') as mock_burn_transaction:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            mock_burn_transaction.return_value = 'burn_transaction_hash'

            target_article_id = self.article_info_table_items[0]['article_id']
            target_tip_value = str(100)

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
            self.assertEqual(json.loads(response['body'])['message'], 'Invalid parameter: Required at least 110 token')

    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__send_tip',
           MagicMock(return_value='0x0000000000000000000000000000000000000000'))
    @patch('private_chain_util.PrivateChainUtil.is_transaction_completed', MagicMock(side_effect=Exception()))
    @patch('me_wallet_tip.MeWalletTip._MeWalletTip__is_burnable_user', MagicMock(return_value=True))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok_with_exception_in_is_transaction_completed(self):
        with patch('me_wallet_tip.UserUtil') as user_util_mock, \
             patch('me_wallet_tip.MeWalletTip._MeWalletTip__burn_transaction') as mock_burn_transaction:
            user_util_mock.get_cognito_user_info.return_value = {
                'UserAttributes': [{
                    'Name': 'custom:private_eth_address',
                    'Value': '0x1111111111111111111111111111111111111111'
                }]
            }
            mock_burn_transaction.return_value = 'burn_transaction_hash'

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
                'burn_transaction': None,  # 途中で処理失敗しているためNoneが入る
                'uncompleted': Decimal(1),
                'sort_key': 1520150552000003,
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
