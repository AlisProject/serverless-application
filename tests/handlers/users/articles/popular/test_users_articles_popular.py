import os
import json
import settings
from unittest import TestCase
from users_articles_popular import UsersArticlesPopular
from tests_util import TestsUtil


class TestUsersArticlesPublic(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        items = [
            {
                'article_id': 'draftId00001',
                'user_id': 'TST',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'popular_sort_key': 9000 * 10**18
            },
            {
                'article_id': 'testid000001',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 2000 * 10 ** 18
            },
            {
                'article_id': 'testid000002',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'price': 200,
                'popular_sort_key': 3000 * 10 ** 18
            },
            {
                'article_id': 'draftid000002',
                'user_id': 'TST',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'price': 200,
                'popular_sort_key': 3500 * 10 ** 18
            },
            {
                'article_id': 'testid000003',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 4000 * 10 ** 18
            },
            {
                'article_id': 'testid000004',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 5000 * 10 ** 18
            }
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = UsersArticlesPopular(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'limit': '2'
            }
        }

        response = UsersArticlesPopular(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000004',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 5000 * 10 ** 18
            },
            {
                'article_id': 'testid000003',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 4000 * 10 ** 18
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_without_limit(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            }
        }

        response = UsersArticlesPopular(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000004',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 5000 * 10 ** 18
            },
            {
                'article_id': 'testid000003',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 4000 * 10 ** 18
            },
            {
                'article_id': 'testid000002',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'price': 200,
                'popular_sort_key': 3000 * 10 ** 18
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), settings.USERS_ARTICLE_POPULAR_INDEX_DEFAULT_LIMIT)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_last_evaluated_key(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'limit': '2',
                'article_id': 'testid000003',
                'popular_sort_key': 4000 * 10 ** 18
            }
        }

        response = UsersArticlesPopular(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000002',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'price': 200,
                'popular_sort_key': 3000 * 10 ** 18
            },
            {
                'article_id': 'testid000001',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 2000 * 10 ** 18
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_only_popular_sort_key(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'popular_sort_key': 5000 * 10 ** 18
            }
        }

        response = UsersArticlesPopular(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000004',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 5000 * 10 ** 18
            },
            {
                'article_id': 'testid000003',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 4000 * 10 ** 18
            },
            {
                'article_id': 'testid000002',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'price': 200,
                'popular_sort_key': 3000 * 10 ** 18
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_only_article_id(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'article_id': 'testid000004'
            }
        }

        response = UsersArticlesPopular(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000004',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 5000 * 10 ** 18
            },
            {
                'article_id': 'testid000003',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'popular_sort_key': 4000 * 10 ** 18
            },
            {
                'article_id': 'testid000002',
                'user_id': 'TST',
                'status': 'public',
                'sort_key': 1520150272000000,
                'price': 200,
                'popular_sort_key': 3000 * 10 ** 18
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_not_exists_target_user(self):
        params = {
            'pathParameters': {
                'user_id': 'HOGE'
            }
        }

        response = UsersArticlesPopular(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 0)

    def test_validation_user_id_required(self):
        params = {
            'pathParameters': {}
        }
        self.assert_bad_request(params)

    def test_validation_user_id_min(self):
        params = {
            'pathParameters': {
                'user_id': 'AL'
            }
        }
        self.assert_bad_request(params)

    def test_validation_user_id_max(self):
        params = {
            'pathParameters': {
                'user_id': 'A' * 51
            }
        }
        self.assert_bad_request(params)

    def test_validation_limit_type(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'limit': 'ALIS'
            }
        }
        self.assert_bad_request(params)

    def test_validation_limit_max(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'limit': '101'
            }
        }
        self.assert_bad_request(params)

    def test_validation_limit_min(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'limit': '0'
            }
        }
        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'article_id': 'A' * 13
            }
        }
        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'article_id': 'A' * 11
            }
        }
        self.assert_bad_request(params)

    def test_validation_popular_sort_key_type(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'popular_sort_key': 'ALIS'
            }
        }
        self.assert_bad_request(params)

    def test_validation_sort_key_max(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'popular_sort_key': 10 ** 24 + 1
            }
        }
        self.assert_bad_request(params)

    def test_validation_sort_key_min(self):
        params = {
            'pathParameters': {
                'user_id': 'TST'
            },
            'queryStringParameters': {
                'popular_sort_key': 10 ** 18 - 1
            }
        }
        self.assert_bad_request(params)
