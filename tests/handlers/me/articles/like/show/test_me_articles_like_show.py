import os
import boto3
import json
from unittest import TestCase
from me_articles_like_show import MeArticleLikeShow
from tests_util import TestsUtil
from unittest.mock import patch, MagicMock


class TestMeArticleLikeShow(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    target_tables = ['ArticleLikedUser']

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
                'user_id': 'test02',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testidlike03',
                'user_id': 'test01',
                'sort_key': 1520150272000002
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_LIKED_USER_TABLE_NAME'], article_liked_user_items)

        # create article_info_table
        article_info_table_items = [
            {
                'article_id': 'testidlike01',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testidlike02',
                'status': 'public',
                'sort_key': 1520150272000001
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        me_articles_like_show = MeArticleLikeShow(params, {}, self.dynamodb)
        response = me_articles_like_show.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok_with_liked_article(self):
        params = {
            'pathParameters': {
                'article_id': 'testidlike01'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        response = MeArticleLikeShow(params, {}, self.dynamodb).main()

        expected_item = {
            'liked': True
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    def test_main_ok_with_not_liked_article(self):
        params = {
            'pathParameters': {
                'article_id': 'testidlike02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        response = MeArticleLikeShow(params, {}, self.dynamodb).main()

        expected_item = {
            'liked': False
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'testidlike02'
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
        with patch('me_articles_like_show.DBUtil', mock_lib):
            response = MeArticleLikeShow(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertEqual(kwargs['status'], 'public')

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_article_id_required(self):
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
