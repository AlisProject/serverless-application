from unittest import TestCase
from article_info_recent import ArticleInfoRecent
from unittest.mock import patch, MagicMock
import yaml
import os
import boto3
import json


class TestArticleInfoRecent(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        os.environ['ARTICLE_INFO_TABLE_NAME'] = 'ArticleInfo'

        f = open("./database.yaml", "r+")
        template = yaml.load(f)
        f.close()

        create_params = {'TableName': 'ArticleInfo'}
        create_params.update(template['Resources']['ArticleInfo']['Properties'])
        cls.dynamodb.create_table(**create_params)

        table = TestArticleInfoRecent.dynamodb.Table('ArticleInfo')
        items = [
            {
                'article_id': 'draftId00001',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'status': 'public',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000003',
                'status': 'public',
                'sort_key': 1520150272000003
            }
        ]

        for item in items:
            table.put_item(Item=item)

    @classmethod
    def tearDownClass(cls):
        table = TestArticleInfoRecent.dynamodb.Table('ArticleInfo')
        table.delete()

    def assert_bad_request(self, params):
        function = ArticleInfoRecent(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '1'
            }
        }

        response = ArticleInfoRecent(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000003',
                'status': 'public',
                'sort_key': 1520150272000003
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_no_limit(self):
        table = TestArticleInfoRecent.dynamodb.Table('ArticleInfo')

        for i in range(21):
            table.put_item(Item={
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i
                }
            )

        params = {
            'queryStringParameters': {}
        }
        response = ArticleInfoRecent(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 20)

    def test_main_ok_with_evaluated_key(self):
        params = {
            'queryStringParameters': {
                'limit': '100',
                'article_id': 'testid000001',
                'sort_key': '1520150272000002'
            }
        }

        response = ArticleInfoRecent(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    @patch("article_info_recent.validate", MagicMock(side_effect=Exception()))
    def test_main_ng_with_internal_server_error(self):
        params = {
            'queryStringParameters': {
                'limit': '2'
            }
        }

        response = ArticleInfoRecent(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 500)

    def test_validation_with_no_params(self):
        params = {}

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
