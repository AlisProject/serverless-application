from elasticsearch import Elasticsearch
from search_users import SearchUsers
from unittest import TestCase
import json


class TestSearchUsers(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        items = []
        for dummy in range(30):
            items.append({
                'user_id': f"testuser{dummy}",
                'user_display_name': f"testuser",
                'updated_at': 1530112753,
            })
        for item in items:
            self.elasticsearch.index(
                    index="users",
                    doc_type="user",
                    id=item["user_id"],
                    body=item
            )
            self.elasticsearch.indices.refresh(index="users")

    def tearDown(self):
        self.elasticsearch.indices.delete(index="users", ignore=[404])

    def test_search_request(self):
        params = {
                'queryStringParameters': {
                    'limit': '1',
                    'query': 'testuser1'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 1)

    def test_search_request_limit(self):
        # limit 指定なし
        params = {
                'queryStringParameters': {
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 20)
        # limit 指定
        params = {
                'queryStringParameters': {
                    'limit': '10',
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 10)

    def test_search_request_page(self):
        # page 指定なし
        params = {
                'queryStringParameters': {
                    'limit': '20',
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 20)
        # page 指定
        params = {
                'queryStringParameters': {
                    'page': '2',
                    'limit': '20',
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 10)
        # page 範囲外
        params = {
                'queryStringParameters': {
                    'page': '100001',
                    'limit': '20',
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_search_request_offset(self):
        # offset 指定
        params = {
                'queryStringParameters': {
                    'limit': '10',
                    'page': '3',
                    'offset': '5',
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 5)
        # offset 指定のみ
        params = {
                'queryStringParameters': {
                    'offset': '28',
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 2)

    def test_search_match_zero(self):
        params = {
                'queryStringParameters': {
                    'query': 'hogehoge'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 0)

    def test_search_request_query_over150(self):
        # query文字列150超
        params = {
                'queryStringParameters': {
                    'query': 'abcdefghij' * 16
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_offset_type(self):
        params = {
            'queryStringParameters': {
                'query': 'hogehoge',
                'offset': 'A'
            }
        }

        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_offset_max(self):
        params = {
            'queryStringParameters': {
                'query': 'hogehoge',
                'offset': '101'
            }
        }

        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_offset_min(self):
        params = {
            'queryStringParameters': {
                'query': 'hogehoge',
                'offset': '-1'
            }
        }

        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)
