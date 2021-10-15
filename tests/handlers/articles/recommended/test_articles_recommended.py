import json
import os
from unittest import TestCase

from tests_util import TestsUtil

from articles_recommended import ArticlesRecommended


class TestArticlesRecommended(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.delete_all_tables(self.dynamodb)
        TestsUtil.set_all_tables_name_to_env()

        self.article_info_items = [
            {
                'article_id': 'testid000001',
                'user_id': 'matsumatsu20',
                'created_at': 1520150272,
                'title': 'title',
                'overview': 'overview',
                'status': 'public',
                'topic': 'crypto',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'user_id': 'matsumatsu20',
                'created_at': 1520150272,
                'title': 'title',
                'overview': 'overview',
                'status': 'public',
                'topic': 'crypto',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000003',
                'user_id': 'matsumatsu20',
                'created_at': 1520150272,
                'title': 'title',
                'overview': 'overview',
                'status': 'public',
                'topic': 'crypto',
                'sort_key': 1520150272000003
            },
            {
                'article_id': 'testid000004',
                'user_id': 'matsumatsu20',
                'created_at': 1520150272,
                'title': 'title',
                'overview': 'overview',
                'status': 'public',
                'topic': 'crypto',
                'sort_key': 1520150272000003
            },
            {
                'article_id': 'testid000005',
                'user_id': 'matsumatsu20',
                'created_at': 1520150272,
                'title': 'title',
                'overview': 'overview',
                'status': 'public',
                'topic': 'crypto',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000006',
                'user_id': 'matsumatsu20',
                'created_at': 1520150272,
                'title': 'title',
                'overview': 'overview',
                'status': 'public',
                'topic': 'crypto',
                'sort_key': 1520150272000003
            },
            {
                'article_id': 'testid000007',
                'user_id': 'matsumatsu20',
                'created_at': 1520150272,
                'title': 'title',
                'overview': 'overview',
                'status': 'draft',
                'topic': 'crypto',
                'sort_key': 1520150272000003
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['ARTICLE_INFO_TABLE_NAME'],
            self.article_info_items
        )

        eyecatch_articles = [
            {
                'article_type': 'recommended',
                'articles': [article['article_id'] for article in self.article_info_items]
            },
            {
                'article_type': 'blacklisted',
                'articles': ['blacklisted1']
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['SCREENED_ARTICLE_TABLE_NAME'],
            eyecatch_articles
        )

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        article_recommended = ArticlesRecommended(params, {}, dynamodb=self.dynamodb)
        response = article_recommended.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '2'
            }
        }

        response = ArticlesRecommended(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = [self.article_info_items[0], self.article_info_items[1]]

        self.assertEqual(json.loads(response['body'])['Items'], expected)

    def test_main_ok_with_pagination(self):
        params = {
            'queryStringParameters': {
                'limit': '2',
                'page': '2'
            }
        }

        response = ArticlesRecommended(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = [self.article_info_items[2], self.article_info_items[3]]

        self.assertEqual(json.loads(response['body'])['Items'], expected)

    def test_main_ok_with_default_limit(self):
        screened_article_table = self.dynamodb.Table(os.environ['SCREENED_ARTICLE_TABLE_NAME'])
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        recommended_articles = []

        # ArticleInfoの登録
        for i in range(200):
            article = {
                'article_id': 'default000' + str(i),
                'user_id': 'matsumatsu20',
                'status': 'public'
            }
            article_info_table.put_item(Item=article)
            recommended_articles.append('default000' + str(i))

        # オススメ記事の登録
        screened_article_table.put_item(Item={
            'article_type': 'recommended',
            'articles': recommended_articles
        })

        params = {
            'queryStringParameters': {}
        }

        response = ArticlesRecommended(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_main_ok_with_draft_article(self):
        params = {
            'queryStringParameters': {
                'limit': '10'
            }
        }

        response = ArticlesRecommended(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 6)
        self.assertFalse(self.article_info_items[6] in json.loads(response['body'])['Items'])

    def test_main_ok_with_eyecatch_and_blacklisted_articles(self):
        table = self.dynamodb.Table(os.environ['SCREENED_ARTICLE_TABLE_NAME'])
        table.put_item(Item={
            'article_type': 'blacklisted',
            'articles': [self.article_info_items[3]['article_id']]
        })

        params = {
            'queryStringParameters': {
                'limit': '10'
            }
        }

        response = ArticlesRecommended(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = [
            self.article_info_items[0],
            self.article_info_items[1],
            self.article_info_items[2],
            self.article_info_items[4],
            self.article_info_items[5]
        ]

        self.assertEqual(json.loads(response['body'])['Items'], expected)

    def test_main_ok_with_empty_article(self):
        table = self.dynamodb.Table(os.environ['SCREENED_ARTICLE_TABLE_NAME'])

        table.delete_item(Key={'article_type': 'recommended'})
        table.delete_item(Key={'article_type': 'blacklisted'})

        response = ArticlesRecommended({}, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = []

        self.assertEqual(json.loads(response['body'])['Items'], expected)

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
