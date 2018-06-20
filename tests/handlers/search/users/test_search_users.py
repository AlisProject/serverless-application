from elasticsearch import Elasticsearch
from search_users import SearchUsers
from unittest import TestCase
import json


class TestSearchUsers(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        body = {
                'user_id': 'testuser',
                'user_display_name': 'testuser',
                'updated_at': 1530112753,
                'sync_elasticsearch': 0
        }
        self.elasticsearch.index(
                index="users",
                doc_type="user",
                id="test",
                body=body
        )
        self.elasticsearch.indices.refresh(index="users")

    def tearDown(self):
        self.elasticsearch.indices.delete(index="users", ignore=[404])

    def test_search_request(self):
        params = {
                'queryStringParameters': {
                    'limit': '1',
                    'query': 'testuser'
                }
        }
        response = SearchUsers(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 1)
