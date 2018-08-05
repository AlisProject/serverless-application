from unittest import TestCase
from articles_recent import ArticlesRecent
from tests_util import TestsUtil
import os
import json
from elasticsearch import Elasticsearch
from tests_es_util import TestsEsUtil


class TestArticlesRecent(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create article_info_table
        article_info_items = [
            {
                'article_id': 'draftId00001',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'topic': 'crypto'
            },
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001,
                'topic': 'crypto'
            },
            {
                'article_id': 'testid000002',
                'status': 'public',
                'sort_key': 1520150272000002,
                'topic': 'crypto'
            },
            {
                'article_id': 'testid000003',
                'status': 'public',
                'sort_key': 1520150272000003,
                'topic': 'hoge'
            }
        ]

        for i in range(30):
            article_info_items.append({
                'article_id': 'test_dummy_article-' + str(i),
                'status': 'public',
                'sort_key': 1520150271000000 + i,
                'topic': 'dummy'
            })

        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        TestsEsUtil.create_articles_index(cls.elasticsearch)
        TestsEsUtil.sync_public_articles_from_dynamodb(cls.dynamodb, cls.elasticsearch)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)
        TestsEsUtil.remove_articles_index(cls.elasticsearch)

    def assert_bad_request(self, params):
        function = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '1'
            }
        }

        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        expected_items = [
            {
                'article_id': 'testid000003',
                'status': 'public',
                'sort_key': 1520150272000003,
                'topic': 'hoge'
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_no_limit(self):
        params = {
            'queryStringParameters': None
        }
        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 20)

    def test_main_ok_search_by_topic(self):
        params = {
            'queryStringParameters': {
                'limit': '10',
                'topic': 'crypto'
            }
        }

        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        expected_items = [
            {
                'article_id': 'testid000002',
                'status': 'public',
                'sort_key': 1520150272000002,
                'topic': 'crypto'
            },
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001,
                'topic': 'crypto'
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_no_page(self):
        params = {
            'queryStringParameters': {
                'limit': '20',
                'topic': 'dummy'
            }
        }
        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 20)

    def test_main_ok_with_page(self):
        params = {
            'queryStringParameters': {
                'limit': '20',
                'page': '2',
                'topic': 'dummy'
            }
        }
        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_main_ok_exceed_page(self):
        params = {
            'queryStringParameters': {
                'limit': '20',
                'page': '3',
                'topic': 'dummy'
            }
        }
        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 0)

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

    def test_validation_too_long_topic(self):
        params = {
            'queryStringParameters': {
                'topic': 'A' * 21
            }
        }

        self.assert_bad_request(params)

    def test_validation_invalid_page(self):
        params = {
            'queryStringParameters': {
                'page': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_too_big_page(self):
        params = {
            'queryStringParameters': {
                'page': '100001'
            }
        }

        self.assert_bad_request(params)
