import os
import json
from unittest import TestCase

from me_articles_purchased_article_ids_index import MeArticlesPurchasedArticleIdsIndex
from tests_util import TestsUtil


class TestMeArticlesPurchasedArticleIdsIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        cls.articles_purchased_items = [
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000000,
                'history_created_at': 1520150272,
                'created_at': 1520150272,
                'transaction': '0x0000000000000000000000000000000000000000',
                'status': 'done',
                'price': 100
            },
            {
                'article_id': 'publicId0002',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_02',
                'sort_key': 1520150272000001,
                'history_created_at': 1520150273,
                'created_at': 1520150273,
                'transaction': '0x0000000000000000000000000000000000000001',
                'status': 'done',
                'price': 200
            },
            {
                'article_id': 'publicId0003',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000002,
                'history_created_at': 1520150274,
                'created_at': 1520150274,
                'transaction': '0x0000000000000000000000000000000000000002',
                'status': 'done',
                'price': 300
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLES_PURCHASED_TABLE_NAME'], cls.articles_purchased_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        response = MeArticlesPurchasedArticleIdsIndex(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01'
                    }
                }
            }
        }

        response = MeArticlesPurchasedArticleIdsIndex(event=params, context={}, dynamodb=self.dynamodb).main()

        expected_items = [self.articles_purchased_items[0]['article_id'], self.articles_purchased_items[2]['article_id']]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(sorted(json.loads(response['body'])['article_ids']), sorted(expected_items))

    def test_main_with_no_articles_purchased(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_03'
                    }
                }
            }
        }

        response = MeArticlesPurchasedArticleIdsIndex(event=params, context={}, dynamodb=self.dynamodb).main()

        expected_items = []

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['article_ids'], expected_items)
