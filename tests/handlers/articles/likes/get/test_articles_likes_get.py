import os
import boto3
from unittest import TestCase
from articles_likes_get import ArticlesLikesGet
from tests_util import TestsUtil


class TestArticlesLikesGet(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create article_liked_user_table
        article_liked_user_items = [
            {
                'article_id': 'testidlike01',
                'user_id': 'test01',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testidlike02',
                'user_id': 'test01',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testidlike02',
                'user_id': 'test02',
                'sort_key': 1520150272000002
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_LIKED_USER_TABLE_NAME'], article_liked_user_items)

        # create article_info_table
        article_info_table_items = [
            {
                'article_id': 'testidlike00',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testidlike01',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testidlike02',
                'status': 'public',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000003',
                'status': 'draft',
                'sort_key': 1520150272000002
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        test_function = ArticlesLikesGet(params, {}, self.dynamodb)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok_like_0(self):
        params = {
            'pathParameters': {
                'article_id': 'testidlike00'
            }
        }

        article_liked_user = ArticlesLikesGet(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['Count'], 0)

    def test_main_ok_like_1(self):
        params = {
            'pathParameters': {
                'article_id': 'testidlike01'
            }
        }

        article_liked_user = ArticlesLikesGet(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['Count'], 1)

    def test_main_ok_like_2(self):
        params = {
            'pathParameters': {
                'article_id': 'testidlike02'
            }
        }

        article_liked_user = ArticlesLikesGet(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['Count'], 2)

    def test_main_ng_status_draft(self):
        params = {
            'pathParameters': {
                'article_id': 'testidlike03'
            }
        }

        article_liked_user = ArticlesLikesGet(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 13
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 11
            }
        }

        self.assert_bad_request(params)

    def test_validation_not_exists_article_id(self):
        params = {
            'pathParameters': {
                'article_id': 'a' * 12
            }
        }

        article_liked_user = ArticlesLikesGet(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        self.assertEqual(response['statusCode'], 400)
