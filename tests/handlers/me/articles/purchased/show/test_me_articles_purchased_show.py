import os
import json
from unittest import TestCase
from me_articles_purchased_show import MeArticlesPurchasedShow
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesPurchasedShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        article_info_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'status': 'public',
                'sort_key': 1520150272000000,
                'overview': 'sample_overview1',
                'eye_catch_url': 'http://example.com/eye_catch_url',
                'price': 100
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'test02',
                'status': 'public',
                'sort_key': 1520150272000001,
                'overview': 'sample_overview2',
                'eye_catch_url': 'http://example.com/eye_catch_url',
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_content_items = [
            {
                'article_id': 'publicId0001',
                'title': 'sample_title1',
                'body': 'sample_body1',
                'paid_body': 'sample_paid_body1'
            },
            {
                'article_id': 'publicId0002',
                'title': 'sample_title2',
                'body': 'sample_body2',
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

        paid_articles_items = [
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test01',
                'user_id': 'paid_user_id_01',
                'history_created_at': 1520150272,
                'created_at': 1520150272,
                'transaction': '0x0000000000000000000000000000000000000000',
                'status': 'done',
                'sort_key': 1520150272000000,
                'price': 100,
            },
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test01',
                'user_id': 'paid_user_id_02',
                'history_created_at': 1520150273,
                'created_at': 1520150272,
                'transaction': '0x0000000000000000000000000000000000000001',
                'status': 'doing',
                'sort_key': 1520150272000001,
                'price': 100,
            },
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test01',
                'user_id': 'paid_user_id_01',
                'history_created_at': 1520150271,
                'created_at': 1520150271,
                'transaction': '0x0000000000000000000000000000000000000002',
                'status': 'fail',
                'sort_key': 1520150271000001,
                'price': 100
            },
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test01',
                'user_id': 'paid_user_id_03',
                'history_created_at': 1520150271,
                'created_at': 1520150275,
                'transaction': '0x0000000000000000000000000000000000000002',
                'status': 'doing',
                'sort_key': 1520150275000001,
                'price': 100
            },
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test01',
                'user_id': 'paid_user_id_03',
                'history_created_at': 1520150271,
                'created_at': 1520150276,
                'transaction': '0x0000000000000000000000000000000000000002',
                'status': 'fail',
                'sort_key': 1520150276000001,
                'price': 100
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], paid_articles_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesPurchasedShow(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'paid_user_id_01'
                    }
                }
            }
        }

        response = MeArticlesPurchasedShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'publicId0001',
            'user_id': 'test01',
            'title': 'sample_title1',
            'body': 'sample_paid_body1',
            'status': 'public',
            'overview': 'sample_overview1',
            'sort_key': 1520150272000000,
            'eye_catch_url': 'http://example.com/eye_catch_url',
            'price': 100
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
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_purchased_show.DBUtil', mock_lib):
            MeArticlesPurchasedShow(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertEqual(kwargs['status'], 'public')
            self.assertTrue(kwargs['is_purchased'])

    def test_validation_not_paid_user(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'not_paid_user_id'
                    }
                }
            }
        }

        response = MeArticlesPurchasedShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 403)

    def test_validation_status_is_not_done(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'paid_user_id_02'
                    }
                }
            }
        }

        response = MeArticlesPurchasedShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 403)

    # statusがdoneのpaid_articleが一件の場合
    def test_validation_status_is_done(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'paid_user_id_01'
                    }
                }
            }
        }

        response = MeArticlesPurchasedShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

    # statusがdoneのpaidarticleが一件も存在しない場合
    def test_all_paid_article_status_not_done(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'paid_user_id_03'
                    }
                }
            }
        }

        response = MeArticlesPurchasedShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 403)

    def test_validation_with_no_params(self):
        params = {
            'pathParameters': {}
        }

        self.assert_bad_request(params)

    def test_validation_not_article_exists(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0003'
            }
        }

        response = MeArticlesPurchasedShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 404)

    def test_validation_not_paid_article(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            }
        }

        response = MeArticlesPurchasedShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 404)

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
