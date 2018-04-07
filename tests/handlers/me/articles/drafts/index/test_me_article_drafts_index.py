import os
import json
from unittest import TestCase
from me_articles_drafts_index import MeArticlesDraftsIndex
from tests_util import TestsUtil


class TestMeArticlesDraftsIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test_user_id',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'user_id': 'test_user_id',
                'status': 'draft',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'user_id': 'test_user_id',
                'status': 'draft',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000003',
                'user_id': 'test_user_id2',
                'status': 'draft',
                'sort_key': 1520150272000003
            },
            {
                'article_id': 'testid000004',
                'user_id': 'test_user_id',
                'status': 'draft',
                'sort_key': 1520150272000004
            }
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesDraftsIndex(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '2'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        response = MeArticlesDraftsIndex(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000004',
                'user_id': 'test_user_id',
                'status': 'draft',
                'sort_key': 1520150272000004
            },
            {
                'article_id': 'testid000002',
                'user_id': 'test_user_id',
                'status': 'draft',
                'sort_key': 1520150272000002
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_evaluated_key(self):
        params = {
            'queryStringParameters': {
                'limit': '3',
                'article_id': 'testid000002',
                'sort_key': '1520150272000002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        response = MeArticlesDraftsIndex(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000001',
                'user_id': 'test_user_id',
                'status': 'draft',
                'sort_key': 1520150272000001
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_only_sort_key(self):
        params = {
            'queryStringParameters': {
                'sort_key': '1520150272000002',
                'limit': '1'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        response = MeArticlesDraftsIndex(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000001',
                'user_id': 'test_user_id',
                'status': 'draft',
                'sort_key': 1520150272000001
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertNotEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_evaluated_key_with_no_limit(self):
        table = self.dynamodb.Table('ArticleInfo')

        for i in range(11):
            table.put_item(Item={
                'user_id': 'test_user_id',
                'article_id': 'test_limit_number' + str(i),
                'status': 'draft',
                'sort_key': 1520150273000000 + i
                }
            )

        params = {
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        response = MeArticlesDraftsIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_main_with_no_recource(self):
        params = {
            'queryStringParameters': {
                'limit': '3'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'not_exists_user_id'
                    }
                }
            }
        }

        response = MeArticlesDraftsIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], [])

    def test_validation_with_no_query_params(self):
        params = {
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        response = MeArticlesDraftsIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

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

    def test_validation_sort_key_type(self):
        params = {
            'queryStringParameters': {
                'sort_key': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_max(self):
        params = {
            'queryStringParameters': {
                'sort_key': '2147483647000001'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_min(self):
        params = {
            'queryStringParameters': {
                'article_id': '0'
            }
        }

        self.assert_bad_request(params)
