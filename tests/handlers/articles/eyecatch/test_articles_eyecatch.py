import json
import os
from unittest import TestCase

from tests_util import TestsUtil

from articles_eyecatch import ArticlesEyecatch


class TestArticlesEyecatch(TestCase):
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
                'article_type': 'eyecatch',
                'articles': {
                    'test_topic': ['testid000001', 'testid000002', 'testid000003']
                }
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['SCREENED_ARTICLE_TABLE_NAME'],
            eyecatch_articles
        )

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'topic': 'test_topic'
            }
        }
        response = ArticlesEyecatch(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = [self.article_info_items[0], self.article_info_items[1], self.article_info_items[2]]
        self.assertEqual(json.loads(response['body'])['Items'], expected)

    def test_main_ok_with_none_response(self):
        params = {
            'queryStringParameters': {
                'topic': 'test_topic'
            }
        }
        table = self.dynamodb.Table(os.environ['SCREENED_ARTICLE_TABLE_NAME'])
        table.put_item(Item={
            'article_type': 'eyecatch',
            'articles': {
                'test_topic': ['testid000004', 'testid000005', 'testid000003']
            }
        })

        response = ArticlesEyecatch(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = [self.article_info_items[2]]

        self.assertEqual(json.loads(response['body'])['Items'], expected)

    def test_main_ok_with_empty_article(self):
        table = self.dynamodb.Table(os.environ['SCREENED_ARTICLE_TABLE_NAME'])

        params = {
            'queryStringParameters': {
                'topic': 'test_topic'
            }
        }

        table.delete_item(Key={'article_type': 'eyecatch'})

        response = ArticlesEyecatch(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = []

        self.assertEqual(json.loads(response['body'])['Items'], expected)

        table.put_item(Item={
            'article_type': 'eyecatch',
            'articles': {}
        })

        response = ArticlesEyecatch(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = []

        self.assertEqual(json.loads(response['body'])['Items'], expected)

        table.put_item(Item={
            'article_type': 'eyecatch',
            'articles': {
                'not_exists': ['testid000001', 'testid000002', 'testid000003']
            }
        })

        response = ArticlesEyecatch(params, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

        expected = []

        self.assertEqual(json.loads(response['body'])['Items'], expected)
