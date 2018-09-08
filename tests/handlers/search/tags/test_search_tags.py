import json
from unittest import TestCase

from tests_es_util import TestsEsUtil

from search_tags import SearchTags
from elasticsearch import Elasticsearch


class TestSearchTags(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        TestsEsUtil.create_tag_index(self.elasticsearch)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'ALIS', 1)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'alis alis', 2)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'alismedia', 3)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'hoge', 4)

        self.elasticsearch.indices.refresh(index='tags')

    def tearDown(self):
        self.elasticsearch.indices.delete(index='tags', ignore=[404])

    def test_search_request(self):
        params = {
                'queryStringParameters': {
                    'query': 'ali'
                }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEquals(len(result), 3)
        self.assertEquals([tag['name'] for tag in result], ['alismedia', 'alis alis', 'ALIS'])

    def test_search_request_with_limit_and_page(self):
        params = {
                'queryStringParameters': {
                    'query': 'ali',
                    'limit': 1,
                    'page': 2
                }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEquals(len(result), 1)
        self.assertEquals([tag['name'] for tag in result], ['alis alis'])

    def test_search_request_with_default_limit(self):
        # 0~110のループ
        for n in range(0, 111):
            TestsEsUtil.create_tag_with_count(self.elasticsearch, 'ALIS' + str(n), n)

        params = {
                'queryStringParameters': {
                    'query': 'ali'
                }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEquals(len(result), 100)
        self.assertEquals(result[0]['name'], 'ALIS110')

    def test_search_request_with_invalid_params(self):
        # query文字列150超
        params = {
                'queryStringParameters': {}
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        # query文字列150超
        params = {
            'queryStringParameters': {
                'query': 'A' * 151
            }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        # page > 100000
        params = {
            'queryStringParameters': {
                'page': '100001',
                'limit': '10',
                'query': 'dummy'
            }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        # page is not integer
        params = {
            'queryStringParameters': {
                'page': 'ALIS',
                'limit': '10',
                'query': 'dummy'
            }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        # limit > 100
        params = {
            'queryStringParameters': {
                'page': '1',
                'limit': '101',
                'query': 'dummy'
            }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        # limit is not integer
        params = {
            'queryStringParameters': {
                'page': '1',
                'limit': 'ALIS',
                'query': 'dummy'
            }
        }
        response = SearchTags(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)
