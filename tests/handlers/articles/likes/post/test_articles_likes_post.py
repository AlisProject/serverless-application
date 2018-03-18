import yaml
import os
import boto3
from unittest import TestCase
from articles_likes_post import ArticlesLikesPost
from unittest.mock import patch, MagicMock
from boto3.dynamodb.conditions import Key


article_liked_user_table_name = 'ArticleLikedUser'


class TestArticlesLikesPost(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        article_liked_user_table_name = 'ArticleLikedUser'
        os.environ['ARTICLE_LIKED_USER_TABLE_NAME'] = article_liked_user_table_name

        f = open('./database.yaml', 'r+')
        template = yaml.load(f)
        f.close()

        create_params = {'TableName': article_liked_user_table_name}
        create_params.update(template['Resources'][article_liked_user_table_name]['Properties'])
        cls.dynamodb.create_table(**create_params)

        table = cls.dynamodb.Table(article_liked_user_table_name)
        cls.items = [
            {
                'article_id': 'testid000000',
                'user_id': 'test01',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'user_id': 'test02',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'user_id': 'test03',
                'sort_key': 1520150272000002
            }
        ]

        for item in cls.items:
            table.put_item(Item=item)

    @classmethod
    def tearDownClass(cls):
        table = cls.dynamodb.Table(article_liked_user_table_name)
        table.delete()

    def assert_bad_request(self, params):
        test_function = ArticlesLikesPost(params, {}, self.dynamodb)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('time.time', MagicMock(return_value=1520150272000003))
    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'a' * 12
            },
            'requestContext': {
                'authorizer': {
                    'cognito:username': 'test04'
                }
            }
        }

        article_liked_user_table = self.dynamodb.Table(article_liked_user_table_name)
        article_liked_user_before = article_liked_user_table.scan()['Items']

        article_liked_user = ArticlesLikesPost(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        article_liked_user_after = article_liked_user_table.scan()['Items']

        target_article_id = params['pathParameters']['article_id']
        target_user_id = params['requestContext']['authorizer']['cognito:username']

        article_liked_user = self.get_article_liked_user(target_article_id, target_user_id)

        expected_items = {
            'article_id': target_article_id,
            'user_id': target_user_id,
            'created_at': 1520150272000003,
            'sort_key': 1520150272000003000000
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_liked_user_after), len(article_liked_user_before) + 1)
        article_liked_user_param_names = ['article_id', 'user_id', 'created_at', 'sort_key']
        for key in article_liked_user_param_names:
            self.assertEqual(expected_items[key], article_liked_user[key])

    @patch('time.time', MagicMock(return_value=1520150272000004))
    def test_main_ok_exist_article_id(self):
        params = {
            'pathParameters': {
                'article_id': self.items[0]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'cognito:username': 'test05'
                }
            }
        }

        article_liked_user_table = self.dynamodb.Table(article_liked_user_table_name)
        article_liked_user_before = article_liked_user_table.scan()['Items']

        article_liked_user = ArticlesLikesPost(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        article_liked_user_after = article_liked_user_table.scan()['Items']

        target_article_id = params['pathParameters']['article_id']
        target_user_id = params['requestContext']['authorizer']['cognito:username']

        article_liked_user = self.get_article_liked_user(target_article_id, target_user_id)

        expected_items = {
            'article_id': target_article_id,
            'user_id': target_user_id,
            'created_at': 1520150272000004,
            'sort_key': 1520150272000004000000
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_liked_user_after), len(article_liked_user_before) + 1)
        article_liked_user_param_names = ['article_id', 'user_id', 'created_at', 'sort_key']
        for key in article_liked_user_param_names:
            self.assertEqual(expected_items[key], article_liked_user[key])

    def test_main_ng_exist_user_id(self):
        params = {
            'pathParameters': {
                'article_id': self.items[0]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'cognito:username': self.items[0]['user_id']
                }
            }
        }

        response = ArticlesLikesPost(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 13
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 11
            }
        }

        self.assert_bad_request(params)

    def get_article_liked_user(self, article_id, user_id):
        query_params = {
            'KeyConditionExpression': Key('article_id').eq(article_id) & Key('user_id').eq(user_id)
        }
        article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
        return article_liked_user_table.query(**query_params)['Items'][0]
