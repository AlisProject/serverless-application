import yaml
import os
import boto3
from unittest import TestCase
from post_confirmation import PostConfirmation
from tests_util import TestsUtil


dynamodb = TestsUtil.get_dynamodb_client()


class TestPostConfirmation(TestCase):

    @classmethod
    def setUpClass(cls):
        user_tables_items = [
            {'user_id': 'testid000000', 'user_display_name': 'testid000000'}
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
        table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        items = table.get_item(Key={"user_id": "hogehoge"})
        self.assertEqual(items['Item']['user_id'], items['Item']['user_display_name'])

    def test_create_userid_already_exists(self):
        event = {'userName': 'testid000000'}
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        response = postconfirmation.main()
        self.assertEqual(response['statusCode'], 500)
