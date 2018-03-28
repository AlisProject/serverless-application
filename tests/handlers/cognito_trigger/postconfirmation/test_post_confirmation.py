import yaml
import os
import boto3
from unittest import TestCase
from post_confirmation import PostConfirmation
from tests_util import TestsUtil


dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')


class TestPostConfirmation(TestCase):
    user_table_name = "Users"

    @classmethod
    def setUpClass(cls):
        user_tables_items = [
            {'user_id': 'testid000000', 'duser_display_name': 'testid000000'}
        ]
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)
        TestsUtil.create_table(dynamodb, os.environ['USERS_TABLE_NAME'], user_tables_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(dynamodb)

    def test_create_userid(self):
        event = {'userName': 'hogehoge'}
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        self.assertEqual(postconfirmation.main(), True)

    def test_create_userid_already_exists(self):
        event = {'userName': 'testid000000'}
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        response = postconfirmation.main()
        self.assertEqual(response['statusCode'], 500)
