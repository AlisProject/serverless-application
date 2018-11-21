from elasticsearch import Elasticsearch
from search_users import SearchUsers
from unittest import TestCase
import json


class TestSearchUsers(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        self.elasticsearch.indices.create(
                index="users",
                body={
                    "settings": {
                        "index": {
                            "number_of_replicas": "0"
                        },
                        "analysis": {
                            "analyzer": {
                                "default": {
                                    "tokenizer": "keyword"
                                }
                            },
                            "normalizer": {
                                "lowcase": {
                                    "type": "custom",
                                    "char_filter": [],
                                    "filter": ["lowercase"]
                                }
                            }
                        }
                    },
                    "mappings": {
                        "user": {
                            "properties": {
                                "user_id": {
                                    "type": "keyword",
                                    "copy_to": "search_name"
                                },
                                "user_display_name": {
                                    "type": "keyword",
                                    "copy_to": "search_name"
                                },
                                "search_name": {
                                    "type": "keyword",
                                    "normalizer": "lowcase"
                                }
                            }
                        }
                    }
                }
        )
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

    def test_search_ignoroecase(self):
        # 大文字小文字を区別しない
        self.elasticsearch.index(
                index="users",
                doc_type="user",
                id="AbCdEfG",
                body={
                    'user_id': "AbCdEfG",
                    'user_display_name': f"HiJkLmN",
                    'updated_at': 1530112761,
                }
        )
        self.elasticsearch.indices.refresh(index="users")
        # abcdeで検索
        params = {
                'queryStringParameters': {
                    'query': 'abcde'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 1)
        # JKLMで検索
        params = {
                'queryStringParameters': {
                    'query': 'JKLM'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 1)
