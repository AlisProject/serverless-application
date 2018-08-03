from unittest import TestCase
from articles_recent import ArticlesRecent
from tests_util import TestsUtil
import os
import json
from elasticsearch import Elasticsearch


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
                'topic': 'crypt'
            },
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001,
                'topic': 'crypt'
            },
            {
                'article_id': 'testid000002',
                'status': 'public',
                'sort_key': 1520150272000002,
                'topic': 'hoge'
            },
            {
                'article_id': 'testid000003',
                'status': 'public',
                'sort_key': 1520150272000003,
                'topic': 'hoge'
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)
        cls.sync_to_elastic_search(article_info_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)
        cls.elasticsearch.indices.delete(index='articles', ignore=[404])

    @classmethod
    def sync_to_elastic_search(cls, articles):
        for article in articles:
            cls.elasticsearch.index(
                    index='articles',
                    doc_type='article',
                    id=article['article_id'],
                    body=article
            )
        cls.elasticsearch.indices.refresh(index='articles')

    def assert_bad_request(self, params):
        function = ArticlesRecent(params, {}, self.dynamodb)
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
        table = TestArticlesRecent.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        es_list = []
        for i in range(21):
            item = {
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i,
                'topic': 'crypt'
            }
            table.put_item(Item=item)
            es_list.append(item)
        TestArticlesRecent.sync_to_elastic_search(es_list)

        params = {
            'queryStringParameters': None
        }
        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 20)

    def test_main_ok_search_by_topic(self):
        params = {
            'queryStringParameters': {
                'limit': '1',
                'topic': 'crypt'
            }
        }

        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        expected_items = [
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001,
                'topic': 'crypt'
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_page(self):
        es_list = []
        for i in range(20):
            es_list.append({
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i,
                'topic': 'crypt'
            })
        TestArticlesRecent.sync_to_elastic_search(es_list)

        params = {
            'queryStringParameters': {
                'limit': '10',
                'topic': 'crypt',
                'page': '2'
            }
        }
        response = ArticlesRecent(params, {}, elasticsearch=self.elasticsearch).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

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
