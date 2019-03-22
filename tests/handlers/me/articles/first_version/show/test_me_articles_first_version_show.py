import os
import json
from unittest import TestCase
from me_articles_first_version_show import MeArticlesFirstVersionShow
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesFirstVersionShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        paid_articles_items = [
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000000,
                'history_created_at': 1520150273,
                'created_at': 1520150272,
                'transaction': '0x0000000000000000000000000000000000000000',
                'status': 'done',
                'price': 100
            },
            {
                'article_id': 'publicId0002',
                'article_user_id': 'test_article_user_02',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000001,
                'history_created_at': 1520150275,
                'created_at': 1520150273,
                'transaction': '0x0000000000000000000000000000000000000001',
                'status': 'doing',
                'price': 100
            },
            {
                'article_id': 'publicId0003',
                'article_user_id': 'test_article_user_03',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000002,
                'history_created_at': 1520150276,
                'created_at': 1520150273,
                'transaction': '0x0000000000000000000000000000000000000002',
                'status': 'done',
                'price': 100
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], paid_articles_items)

        article_history_items = [
            {
                'article_id': 'publicId0001',
                'created_at': 1520150272,
                'body': 'test_body_version_01',
                'title': 'test_title_01'
            },
            {
                'article_id': 'publicId0001',
                'created_at': 1520150273,
                'body': 'test_body_version_02',
                'title': 'test_title_02',
                'price': 100
            },
            {
                'article_id': 'publicId0002',
                'created_at': 1520150274,
                'body': 'test_body_version_03',
                'title': 'test_title_03',
                'price': 200
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_HISTORY_TABLE_NAME'], article_history_items)

        article_info_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test_article_user_01',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'version': 2,
                'price': 200,
                'created_at': 1520150274
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'test_article_user_02',
                'status': 'draft',
                'sort_key': 1520150272000001,
                'version': 2,
                'price': 200,
                'created_at': 1520150272
            },
            {
                'article_id': 'publicId0003',
                'user_id': 'test_article_user_03',
                'status': 'draft',
                'sort_key': 1520150272000002,
                'version': 2,
                'price': 200,
                'created_at': 1520150273
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_content_items = [
            {
                'article_id': 'publicId0001',
                'title': 'sample_title1',
                'body': 'sample_body1',
                'paid_body': 'sample_paid_body1',
                'created_at': 1520150274
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        response = MeArticlesFirstVersionShow(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01'
                    }
                }
            }
        }

        response = MeArticlesFirstVersionShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'publicId0001',
            'user_id': 'test_article_user_01',
            'title': 'test_title_02',
            'body': 'test_body_version_02',
            'status': 'draft',
            'sort_key': 1520150272000000,
            'price': 100,
            'version': 2,
            'created_at': 1520150273
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_first_version_show.DBUtil', mock_lib):
            MeArticlesFirstVersionShow(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['is_purchased'])

    def test_paid_article_forbidden(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_02'
                    }
                }
            }
        }

        response = MeArticlesFirstVersionShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 403)

    def test_paid_article_is_processing(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_02'
                    }
                }
            }
        }

        response = MeArticlesFirstVersionShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 403)

    def test_first_version_article_history_not_found(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0003'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01'
                    }
                }
            }
        }

        response = MeArticlesFirstVersionShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 404)

    def test_validation_with_no_params(self):
        params = {
            'pathParameters': {}
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
