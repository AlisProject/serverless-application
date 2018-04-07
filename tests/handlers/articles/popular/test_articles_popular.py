from unittest import TestCase
from articles_popular import ArticlesPopular
from tests_util import TestsUtil
from unittest.mock import patch, MagicMock
import yaml
import os
import boto3
import json


class TestArticlesPopular(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create article_info_table
        article_info_items = [
            {
                'article_id': 'draftid00001',
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
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_score_items = [
            {
                'article_id': 'draftid00001',
                'score': 24,
                'evaluated_at': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'score': 12,
                'evaluated_at': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'score': 18,
                'evaluated_at': 1520150272000000
            },
            {
                'article_id': 'testid000003',
                'score': 6,
                'evaluated_at': 1520150272000000
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_SCORE_TABLE_NAME'], article_score_items)

        evaluated_manage_items = [
            {'active_evaluated_at': 1520150272000000}
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'], evaluated_manage_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = ArticlesPopular(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '3'
            }
        }

        response = ArticlesPopular(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000002',
                'status': 'public',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001
            }
        ]

        expected_evaluated_key = {
            'article_id': 'testid000001',
            'score': 12,
            'evaluated_at': 1520150272000000
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)
        self.assertEqual(json.loads(response['body'])['LastEvaluatedKey'], expected_evaluated_key)

    def test_main_ok_with_no_limit(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_score_table = self.dynamodb.Table(os.environ['ARTICLE_SCORE_TABLE_NAME'])

        for i in range(21):
            article_info_table.put_item(Item={
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i
                }
            )

            article_score_table.put_item(Item={
                'article_id': 'test_limit_number' + str(i),
                'score': 30,
                'evaluated_at': 1520150272000000
                }
            )

        params = {
            'queryStringParameters': None
        }
        response = ArticlesPopular(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 20)

    def test_main_ok_with_evaluated_key(self):
        params = {
            'queryStringParameters': {
                'limit': '100',
                'article_id': 'testid000001',
                'score': '12'
            }
        }

        response = ArticlesPopular(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000003',
                'status': 'public',
                'sort_key': 1520150272000003
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

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

    def test_validation_score_type(self):
        params = {
            'queryStringParameters': {
                'score': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_score_max(self):
        params = {
            'queryStringParameters': {
                'score': '2147483647000001'
            }
        }

        self.assert_bad_request(params)

    def test_validation_score_min(self):
        params = {
            'queryStringParameters': {
                'score': '0'
            }
        }

        self.assert_bad_request(params)
