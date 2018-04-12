import yaml
import os
import boto3
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
        response = postconfirmation.main()
        table = dynamodb.Table(os.environ['BETA_USERS_TABLE_NAME'])
        items = table.get_item(Key={"email": "test@example.com"})
        self.assertEqual(items['Item']['used'], True)
