import yaml
import os
import boto3
from unittest import TestCase
from post_confirmation import PostConfirmation


dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')


class TestPostConfirmation(TestCase):
    user_table_name = "Users"

    @classmethod
    def setUpClass(cls):
        user_tables_items = [
                {'user_id': 'testid000000', 'email': 'test@example.net'}
                ]
        os.environ['USERS_TABLE_NAME'] = cls.user_table_name
        cls.create_table(cls.user_table_name, user_tables_items)

    @classmethod
    def create_table(cls, table_name, table_items):
        f = open('./database.yaml', 'r+')
        template = yaml.load(f)
        f.close()

        create_params = {'TableName': table_name}
        create_params.update(template['Resources'][table_name]['Properties'])
        dynamodb.create_table(**create_params)

        table = dynamodb.Table(table_name)

        for item in table_items:
            table.put_item(Item=item)

    @classmethod
    def tearDownClass(cls):
        dynamodb.Table(cls.user_table_name).delete()

    def test_create_userid(self):
        event = {'userName': 'hogehoge'}
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        self.assertEqual(postconfirmation.main(), True)

    def test_create_userid_already_exists(self):
        event = {'userName': 'testid000000'}
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        response = postconfirmation.main()
        self.assertEqual(response['statusCode'], 500)
