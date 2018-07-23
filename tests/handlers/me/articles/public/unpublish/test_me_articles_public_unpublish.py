import os
import boto3
from unittest import TestCase
from me_articles_public_unpublish import MeArticlesPublicUnpublish
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesPublicUnpublish(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()

        cls.article_info_table = cls.dynamodb.Table('ArticleInfo')
        cls.article_content_table = cls.dynamodb.Table('ArticleContent')
        cls.article_content_edit_table = cls.dynamodb.Table('ArticleContentEdit')

    def setUp(self):
        TestsUtil.delete_all_tables(self.dynamodb)

        article_info_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'test01',
                'status': 'public',
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_content_items = [
            {
                'article_id': 'publicId0001',
                'title': 'sample_title1',
                'body': 'sample_body1'
            },
            {
                'article_id': 'publicId0002',
                'title': 'sample_title2',
                'body': 'sample_body2'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

        article_content_edit_items = [
            {
                'article_id': 'publicId0002',
                'user_id': 'test01',
                'title': 'sample_title2_edit',
                'body': 'sample_body2_edit',
                'overview': 'sample_overview3_edit',
                'eye_catch_url': 'http://example.com/eye_catch_url3_edit'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'], article_content_edit_items)

    def tearDown(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesPublicUnpublish(params, {}, self.dynamodb)
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
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        article_info_before = self.article_info_table.scan()['Items']
        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        response = MeArticlesPublicUnpublish(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        article_info = self.article_info_table.get_item(Key={'article_id': params['pathParameters']['article_id']})['Item']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['status'], 'draft')
        self.assertEqual(article_info['sync_elasticsearch'], 1)
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), 0)

    def test_main_ok_with_article_content_edit(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01'
                    }
                }
            }
        }

        article_info_before = self.article_info_table.scan()['Items']
        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        response = MeArticlesPublicUnpublish(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        article_info = self.article_info_table.get_item(Key={'article_id': params['pathParameters']['article_id']})['Item']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['status'], 'draft')
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), -1)

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
        with patch('me_articles_public_unpublish.DBUtil', mock_lib):
            MeArticlesPublicUnpublish(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
            self.assertEqual(kwargs['status'], 'public')

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
