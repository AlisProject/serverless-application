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
                'created_at': 1530112710,
                'title': "abc1",
                "published_at": 1530112710,
                'body': "huga test",
                'tags': ['A', 'B', 'C', 'd']
            },
            {
                'article_id': "test2",
                'created_at': 1530112720,
                'title': "abc2",
                "published_at": 1530112720,
                'body': "foo bar",
                'tags': ['c', 'd', 'e', 'abcde']
            },
            {
                'article_id': "test3",
                'created_at': 1530112753,
                'title': "abc2",
                "published_at": 1530112753,
                'body': "foo bar",
                'tags': ['ﾊﾝｶｸ', '＆＄％！”＃', '𪚲🍣𪚲', 'aaa-aaa', 'abcde vwxyz']
            },
            {
                'article_id': "test4",
                'created_at': 1530112700,
                'title': "abc2",
                "published_at": 1530112700,
                'body': "foo bar",
                'tags': ['d']
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
                    'query': 'huga',
                    'tag': 'C'
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
        self.assertRegex(result[0]['article_id'], '^dummy')
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
        self.assertRegex(result[0]['article_id'], '^dummy')
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

    def test_search_with_tag(self):
        params = {
                'queryStringParameters': {
                    'tag': 'A'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(result), 1)

    def test_search_with_tag_half_kana(self):
        params = {
                'queryStringParameters': {
                    'tag': 'ﾊﾝｶｸ'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(result), 1)

    def test_search_with_tag_full_symbol(self):
        params = {
                'queryStringParameters': {
                    'tag': '＆＄％！”＃'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(result), 1)

    def test_search_with_tag_emoji(self):
        params = {
                'queryStringParameters': {
                    'tag': '𪚲🍣𪚲'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(result), 1)

    def test_search_with_tag_hyphen(self):
        params = {
                'queryStringParameters': {
                    'tag': 'aaa-aaa'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(result), 1)

    def test_search_with_tag_space(self):
        params = {
                'queryStringParameters': {
                    'tag': 'abcde vwxyz'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(result), 1)

    def test_search_with_tag_sort(self):
        params = {
                'queryStringParameters': {
                    'tag': 'd'
                }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        result = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['published_at'], 1530112720)
        self.assertEqual(result[1]['published_at'], 1530112710)
        self.assertEqual(result[2]['published_at'], 1530112700)

    # Todo: 大文字小文字を区別しない対応
    # def test_search_with_tag_case_insensitive(self):
    #     params = {
    #             'queryStringParameters': {
    #                 'tag': 'c'
    #             }
    #     }
    #     response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
    #     result = json.loads(response['body'])
    #     self.assertEqual(response['statusCode'], 200)
    #     self.assertEqual(len(result), 2)

    def test_search_match_zero(self):
        params = {
                'queryStringParameters': {
                    'tag': 'vwxyz'
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

    def test_search_no_params(self):
        params = {
            'queryStringParameters': {}
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_invalid_tag_parmas(self):
        params = {
            'queryStringParameters': {
                'tag': ''
            }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        params = {
            'queryStringParameters': {
                'tag': 'A' * 26
            }
        }
        response = SearchArticles(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)
