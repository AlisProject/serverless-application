import json
from unittest import TestCase
from search_articles import SearchArticles
from elasticsearch import Elasticsearch


class TestSearchArticles(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        body = {
                'article_id': "test",
                'created_at': 1530112753,
                'title': "abc",
                "published_at": 1530112753,
                'body': "huga test"
        }
        self.elasticsearch.index(
                index="articles",
                doc_type="article",
                id="test",
                body=body
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
