import os
import boto3
import json
from unittest import TestCase
from users_articles_public import UsersArticlesPublic
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestUsersArticlesPublic(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        items = [
            {
                'article_id': 'draftId00001',
                'user_id': 'TST',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000003',
                'user_id': 'TST2',
                'status': 'public',
                'sort_key': 1520150272000003
            },
            {
                'article_id': 'testid000004',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000004
            }
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = UsersArticlesPublic(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'limit': '2'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000004',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000004
            },
            {
                'article_id': 'testid000002',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000002
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_evaluated_key(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'limit': '3',
                'article_id': 'testid000002',
                'sort_key': '1520150272000002'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000001',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000001
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_only_sort_key(self):
        table = self.dynamodb.Table('ArticleInfo')

        for i in range(11):
            table.put_item(Item={
                'user_id': 'test_only_sort_key',
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i
                }
            )

        params = {
            'pathParameters': {
                'user_id': 'test_only_sort_key'
            },
            'queryStringParameters': {
                'sort_key': '1520150272000002'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_main_ok_with_evaluated_key_with_no_limit(self):
        table = self.dynamodb.Table('ArticleInfo')

        for i in range(11):
            table.put_item(Item={
                'user_id': 'TST',
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i
                }
            )

        params = {
            'pathParameters': {
                'user_id': 'TST'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_main_with_no_recource(self):
        params = {
            'pathParameters': {
                'user_id': 'A' * 30
            },
            'queryStringParameters': {
                'limit': '3'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], [])

    def test_validation_with_no_path_params(self):
        params = {
            'queryStringParameters': {
                'limit': '3'
            }
        }

        self.assert_bad_request(params)

    def test_validation_with_no_query_params(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

    def test_validation_user_id_required(self):
        params = {
            'pathParameters': {}
        }

        self.assert_bad_request(params)

    def test_validation_user_id_max(self):
        params = {
            'pathParameters': {
                'user_id': 'AL'
            }
        }

        self.assert_bad_request(params)

    def test_validation_user_id_min(self):
        params = {
            'pathParameters': {
                'user_id': 'A' * 31
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_type(self):
        params = {
            'queryStringParameters': {
                'limit': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_max(self):
        params = {
            'queryStringParameters': {
                'limit': '101'
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_min(self):
        params = {
            'queryStringParameters': {
                'limit': '0'
            }
        }

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

    def test_validation_sort_key_type(self):
        params = {
            'queryStringParameters': {
                'sort_key': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_max(self):
        params = {
            'queryStringParameters': {
                'sort_key': '2147483647000001'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_min(self):
        params = {
            'queryStringParameters': {
                'article_id': '0'
            }
        }

        self.assert_bad_request(params)
