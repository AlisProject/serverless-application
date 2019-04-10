import os
import json
from unittest import TestCase
from me_articles_drafts_show import MeArticlesDraftsShow
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesDraftsShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        article_info_items = [
            {
                'article_id': 'draftId00001',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'draftId00002',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'draftId00003',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'price': 100
            }
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_content_items = [
            {
                'article_id': 'draftId00001',
                'title': 'sample_title1',
                'body': 'sample_body1'
            },
            {
                'article_id': 'publicId0002',
                'title': 'sample_title2',
                'body': 'sample_body2'
            },
            {
                'article_id': 'draftId00003',
                'title': 'sample_title3',
                'body': 'sample_body3',
                'paid_body': 'sample_paid_body3',
            }
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesDraftsShow(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesDraftsShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'draftId00001',
            'user_id': 'test01',
            'status': 'draft',
            'sort_key': 1520150272000000,
            'title': 'sample_title1',
            'body': 'sample_body1'
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_drafts_show.DBUtil', mock_lib):
            MeArticlesDraftsShow(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
            self.assertEqual(kwargs['status'], 'draft')

    def test_main_with_no_article_content(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesDraftsShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'draftId00002',
            'user_id': 'test01',
            'status': 'draft',
            'sort_key': 1520150272000000
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    def test_main_ok_with_paid_body(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00003'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesDraftsShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'draftId00003',
            'body': 'sample_paid_body3',
            'sort_key': 1520150272000000,
            'status': 'draft',
            'title': 'sample_title3',
            'user_id': 'test01',
            'price': 100
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

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
