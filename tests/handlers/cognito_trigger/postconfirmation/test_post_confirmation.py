import os
import boto3
from unittest import TestCase
from post_confirmation import PostConfirmation


dynamodb = boto3.resource('dynamodb')
user_table_name = "Users"


class TestPostConfirmation(TestCase):

    def tablename_to_id(table_name):
        client = boto3.client('cloudformation')
        response = client.list_stack_resources(
                StackName=os.environ['CLOUDFORMATION_STACK_NAME']
                )
        for r in response['StackResourceSummaries']:
            if r['ResourceType'] == 'AWS::DynamoDB::Table' and \
                    r['LogicalResourceId'] == table_name:
                return(r['PhysicalResourceId'])
        return

    def delete_all_items(table_id):
        table = dynamodb.Table(table_id)
        response = table.scan()
        for r in response['Items']:
            table.delete_item(Key={'user_id': r['user_id']})
        return

    @classmethod
    def setUpClass(cls):
        os.environ['USERS_TABLE_NAME'] = cls.tablename_to_id(user_table_name)
        table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        item = {'user_id': 'testid000000', 'user_display_name': 'testid000000'}
        table.put_item(Item=item)

    @classmethod
    def tearDownClass(cls):
        cls.delete_all_items(os.environ['USERS_TABLE_NAME'])

    def test_create_userid(self):
        event = {'userName': 'hogehoge'}
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        self.assertEqual(postconfirmation.main(), True)

    def test_create_userid_already_exists(self):
        event = {'userName': 'testid000000'}
        postconfirmation = PostConfirmation(event=event, context="", dynamodb=dynamodb)
        response = postconfirmation.main()
        self.assertEqual(response['statusCode'], 500)
