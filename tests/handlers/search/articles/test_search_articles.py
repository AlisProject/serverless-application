import json
from unittest import TestCase
from search_articles import SearchArticles
from elasticsearch import Elasticsearch


class TestSearchArticles(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        items = [
                {
                    'article_id': "test1",
                    'created_at': 1530112753,
                    'title': "abc1",
                    "published_at": 1530112753,
                    'body': "huga test"
                },
                {
                    'article_id': "test2",
                    'created_at': 1530112753,
                    'title': "abc2",
                    "published_at": 1530112753,
                    'body': "foo bar"
                }
        ]
        for dummy in range(30):
            items.append({
                'article_id': f"dummy{dummy}",
                'created_at': 1530112753,
                'title': f"abc{dummy}",
                "published_at": 1530112753 + dummy,
                'body': "dummy article{dummy}"
            })
        for item in items:
            self.elasticsearch.index(
                    index="articles",
                    doc_type="article",
                    id=item["article_id"],
                    body=item
            )
            self.elasticsearch.indices.refresh(index="articles")

    def tearDown(self):
        self.elasticsearch.indices.delete(index="articles", ignore=[404])

    def test_search_request(self):
        params = {
                'queryStringParameters': {
                    'limit': '1',
                    'query': 'huga'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 1)

    def test_search_request_limit(self):
        # limit 指定なし
        params = {
                'queryStringParameters': {
                    'query': 'dummy'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 20)
        # limit 指定
        params = {
                'queryStringParameters': {
                    'limit': '10',
                    'query': 'dummy'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 10)

    def test_search_request_page(self):
        # page 指定なし
        params = {
                'queryStringParameters': {
                    'limit': '10',
                    'query': 'dummy'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]['article_id'], 'dummy29')
        # page 指定
        params = {
                'queryStringParameters': {
                    'page': '2',
                    'limit': '10',
                    'query': 'dummy'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(result[0]['article_id'], 'dummy19')
        self.assertEqual(len(result), 10)
        # page 範囲外
        params = {
                'queryStringParameters': {
                    'page': '100001',
                    'limit': '10',
                    'query': 'dummy'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_search_match_zero(self):
        params = {
                'queryStringParameters': {
                    'query': 'def'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(len(result), 0)

    def test_search_request_query_over150(self):
        # query文字列150超
        params = {
                'queryStringParameters': {
                    'limit': '1',
                    'query': 'abcdefghij' * 16
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)
