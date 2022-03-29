import json
from unittest import TestCase
from search_tags_count import SearchTagsCount
from elasticsearch import Elasticsearch
from unittest.mock import patch, MagicMock


class TestSearchTagsCount(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        items = [
            {
                'article_id': 'test1',
                'created_at': 1530112710,
                'title': 'abc1',
                'published_at': 1530112710,
                'sort_key': 1530112710000000,
                'body': 'huga test',
                'tags': ['A', 'B', 'C']
            },
            {
                'article_id': 'test2',
                'created_at': 1530112720,
                'title': 'abc2',
                'published_at': 1530112710 + 1,
                'sort_key': 1530112720000000,
                'body': 'foo bar',
                'tags': ['A', 'B']
            },
            {
                'article_id': 'test3',
                'created_at': 1530112730,
                'title': 'abc3',
                'published_at': 1530112710 + 2,
                'sort_key': 1530112730000000,
                'body': 'foo bar',
                'tags': ['A']
            },
            {
                'article_id': 'test4',
                'created_at': 1530112740,
                'title': 'abc4',
                'published_at': 1530112710 - 1,
                'sort_key': 1530112700000000,
                'body': 'foo bar',
                'tags': ['A', 'B', 'C']
            },
            {
                'article_id': 'test5',
                'created_at': 1530112750,
                'title': 'abc5',
                'published_at': 1530112710,
                'sort_key': 1530112700000000,
                'body': 'foo bar',
                'tags': ['ﾊﾝｶｸ', '＆＄％！”＃', '𪚲🍣𪚲', 'aaa-aaa', 'abcde vwxyz']
            },
        ]
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

    @patch('time.time', MagicMock(return_value=1530112710 + 86400 * 7))
    def test_search_request(self):
        params = {
                'queryStringParameters': {
                    'tags': ['A', 'B', 'C', 'D']
                }
        }
        response = SearchTagsCount(params, {}, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        expected = [
             {'count': 3, 'tag': 'A'},
             {'count': 2, 'tag': 'B'},
             {'count': 1, 'tag': 'C'},
             {'count': 0, 'tag': 'D'}
        ]
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(expected, actual)

    def test_search_request_not_exists(self):
        params = {
                'queryStringParameters': {
                    'tags': ['あ', 'い', 'う']
                }
        }
        response = SearchTagsCount(params, {}, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        expected = [
            {'count': 0, 'tag': 'あ'},
            {'count': 0, 'tag': 'い'},
            {'count': 0, 'tag': 'う'}
        ]
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(expected, actual)

    @patch('time.time', MagicMock(return_value=1530112710 + 86400 * 7))
    def test_search_with_tag_half_kana(self):
        params = {
                'queryStringParameters': {
                    'tags': ['ﾊﾝｶｸ', '＆＄％！”＃', '𪚲🍣𪚲', 'aaa-aaa', 'abcde vwxyz']
                }
        }
        response = SearchTagsCount(params, {}, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        expected = [
            {'count': 1, 'tag': 'ﾊﾝｶｸ'},
            {'count': 1, 'tag': '＆＄％！”＃'},
            {'count': 1, 'tag': '𪚲🍣𪚲'},
            {'count': 1, 'tag': 'aaa-aaa'},
            {'count': 1, 'tag': 'abcde vwxyz'}
        ]
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(expected, actual)

    def test_search_request_tags_over150(self):
        # tags 数150超
        temp_tags = []
        for i in range(151):
            temp_tags.append('AAA')

        params = {
                'queryStringParameters': {
                    'tags': temp_tags,
                }
        }
        response = SearchTagsCount(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_search_no_params(self):
        params = {
            'queryStringParameters': {}
        }
        response = SearchTagsCount(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_invalid_tag_parmas(self):
        params = {
            'queryStringParameters': {
                'tags': ['']
            }
        }
        response = SearchTagsCount(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        params = {
            'queryStringParameters': {
                'tags': ['A' * 26]
            }
        }
        response = SearchTagsCount(params, {}, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)
