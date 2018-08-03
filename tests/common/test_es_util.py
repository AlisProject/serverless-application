from es_util import ESUtil
from unittest import TestCase
from elasticsearch import Elasticsearch
from tests_util import TestsUtil


class TestESUtil(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    @classmethod
    def setUpClass(cls):
        TestsUtil.create_es_articles_index(cls.elasticsearch)

        items = [
            {
                'article_id': 'test1',
                'created_at': 1530112751,
                'title': 'abc1',
                'published_at': 1530112750,
                'body': 'huga test',
                'topic': 'crypt',
                'sort_key': 1520150273000001
            },
            {
                'article_id': 'test2',
                'created_at': 1530112752,
                'title': 'abc2',
                'published_at': 1530112750,
                'body': 'foo bar',
                'topic': 'food',
                'sort_key': 1520150273000002
            }
        ]
        for dummy in range(30):
            items.append({
                'article_id': f"dummy{dummy}",
                'created_at': 1530112750,
                'title': f"abc{dummy}",
                'published_at': 1530112750,
                'body': f"dummy article{dummy}",
                'topic': 'hoge',
                'sort_key': 1420150273000000
            })

        for item in items:
            cls.elasticsearch.index(
                    index='articles',
                    doc_type='article',
                    id=item['article_id'],
                    body=item
            )
        cls.elasticsearch.indices.refresh(index='articles')

    @classmethod
    def tearDownClass(cls):
        TestsUtil.remove_es_articles_index(cls.elasticsearch)

    def test_search_recent_articles_ok(self):
        params = {}
        limit = 1
        page = 1
        response = ESUtil.search_recent_articles(self.elasticsearch, params, limit, page)

        expected_article = {
            'article_id': 'test2',
            'created_at': 1530112752,
            'title': 'abc2',
            'published_at': 1530112750,
            'body': 'foo bar',
            'topic': 'food',
            'sort_key': 1520150273000002
        }
        article = response['hits']['hits'][0]['_source']

        self.assertEqual(expected_article, article)

    def test_search_recent_articles_next_page_ok(self):
        params = {}
        limit = 1
        page = 2
        response = ESUtil.search_recent_articles(self.elasticsearch, params, limit, page)

        expected_article = {
            'article_id': 'test1',
            'created_at': 1530112751,
            'title': 'abc1',
            'published_at': 1530112750,
            'body': 'huga test',
            'topic': 'crypt',
            'sort_key': 1520150273000001
        }
        article = response['hits']['hits'][0]['_source']

        self.assertEqual(expected_article, article)

    def test_search_recent_articles_by_topic_ok(self):
        params = {
            'topic': 'crypt'
        }
        limit = 1
        page = 1
        response = ESUtil.search_recent_articles(self.elasticsearch, params, limit, page)

        expected_article = {
            'article_id': 'test1',
            'created_at': 1530112751,
            'title': 'abc1',
            'published_at': 1530112750,
            'body': 'huga test',
            'topic': 'crypt',
            'sort_key': 1520150273000001
        }
        article = response['hits']['hits'][0]['_source']

        self.assertEqual(expected_article, article)
