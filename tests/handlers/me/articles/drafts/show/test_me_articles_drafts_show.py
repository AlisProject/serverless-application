import os
import boto3
import json
from unittest import TestCase
from me_articles_drafts_show import MeArticlesDraftsShow
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesDraftsShow(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

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
                        'cognito:username': 'test01'
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
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_drafts_show.DBUtil', mock_lib):
            response = MeArticlesDraftsShow(params, {}, self.dynamodb).main()
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
                        'cognito:username': 'test01'
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

    @patch("me_articles_drafts_show.validate", MagicMock(side_effect=Exception()))
    def test_main_ng_with_internal_server_error(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        response = MeArticlesDraftsShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 500)

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
