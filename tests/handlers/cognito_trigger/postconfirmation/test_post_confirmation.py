import os
from unittest import TestCase
from post_confirmation import PostConfirmation
from tests_util import TestsUtil
from unittest.mock import patch, MagicMock


dynamodb = TestsUtil.get_dynamodb_client()


class TestPostConfirmation(TestCase):

    @classmethod
    def setUpClass(cls):
        user_tables_items = [
            {'user_id': 'testid000000', 'user_display_name': 'testid000000'}
        ]
        beta_tables = [
            {'email': 'test@example.com', 'used': False},
        ]
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)
        TestsUtil.create_table(dynamodb, os.environ['USERS_TABLE_NAME'], user_tables_items)
        TestsUtil.create_table(dynamodb, os.environ['BETA_USERS_TABLE_NAME'], beta_tables)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(dynamodb)

    @patch("post_confirmation.PostConfirmation._PostConfirmation__wallet_initialization",
           MagicMock(return_value=True))
    def test_create_userid(self):
        os.environ['BETA_MODE_FLAG'] = "0"
        event = {
                'userName': 'hogehoge',
                'request': {
                    'userAttributes': {
                        'phone_number': '',
                        'email': 'already@example.com'
                    }
                }
        }
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        self.assertEqual(postconfirmation.main(), True)
        table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        items = table.get_item(Key={"user_id": "hogehoge"})
        self.assertEqual(items['Item']['user_id'], items['Item']['user_display_name'])
        self.assertEqual(items['Item']['sync_elasticsearch'], 1)

    @patch("post_confirmation.PostConfirmation._PostConfirmation__wallet_initialization",
           MagicMock(return_value=True))
    def test_create_userid_already_exists(self):
        os.environ['BETA_MODE_FLAG'] = "0"
        event = {
                'userName': 'testid000000',
                'request': {
                    'userAttributes': {
                        'phone_number': '',
                        'email': 'already@example.com'
                    }
                }
        }
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        response = postconfirmation.main()
        self.assertEqual(response['statusCode'], 500)

    @patch("post_confirmation.PostConfirmation._PostConfirmation__wallet_initialization",
           MagicMock(return_value=True))
    def test_beta_user_confirm(self):
        os.environ['BETA_MODE_FLAG'] = "1"
        event = {
                'userName': 'hugahuga',
                'request': {
                    'userAttributes': {
                        'phone_number': '',
                        'email': 'test@example.com'
                    }
                }
        }
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        postconfirmation.main()
        table = dynamodb.Table(os.environ['BETA_USERS_TABLE_NAME'])
        items = table.get_item(Key={"email": "test@example.com"})
        self.assertEqual(items['Item']['used'], True)

    # BUGFIX: ALIS-893
    @patch("post_confirmation.PostConfirmation._PostConfirmation__create_new_account",
           MagicMock(side_effect=Exception()))
    def test_when_wallet_exists(self):
        os.environ['BETA_MODE_FLAG'] = "0"

        # すでに `custom:private_eth_address` を持っている場合
        # パスワード再発行時にこのような値が渡される
        event = {
            'userName': 'foobar',
            'request': {
                'userAttributes': {
                    'phone_number': '',
                    'email': 'test@example.com',
                    "custom:private_eth_address": "0x5d7743a4a6f21593ff6d3d81595f270123456789"
                }
            }
        }
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)

        # `custom:private_eth_address` は更新されないこと
        # (LocalStackがCognito対応していないため、MagicMockで設定した例外がスローされないことで検証を担保している)
        self.assertEqual(postconfirmation.main(), True)
        table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        items = table.get_item(Key={"user_id": "foobar"})
        self.assertEqual(items['Item']['user_id'], items['Item']['user_display_name'])

    # BUGFIX: ALIS-893
    @patch("post_confirmation.PostConfirmation._PostConfirmation__create_new_account",
           MagicMock(side_effect=Exception()))
    def test_when_wallet_not_exists(self):
        os.environ['BETA_MODE_FLAG'] = "0"

        # まだ `custom:private_eth_address` を持っていない場合
        # ユーザ新規作成時にこのような値が渡される
        event = {
            'userName': 'foobar',
            'request': {
                'userAttributes': {
                    'phone_number': '',
                    'email': 'test@example.com'
                }
            }
        }
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)

        # `custom:private_eth_address` はが更新されること
        # (LocalStackがCognito対応していないため、MagicMockで設定した例外がスローされることで検証を担保している)
        with self.assertRaises(Exception):
            self.assertEqual(postconfirmation.main(), True)
