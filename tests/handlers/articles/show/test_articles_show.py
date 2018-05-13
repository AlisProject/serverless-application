from unittest import TestCase
from articles_show import ArticlesShow
from tests_util import TestsUtil
from unittest.mock import patch, MagicMock
import os
import json


class TestArticlesShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create article_info_table
        cls.article_info_table_items = [
            {
                'article_id': 'testid000001',
                'status': 'public',
                'title': 'testid000001 titile',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'status': 'public',
                'title': 'testid000002 titile',
                'sort_key': 1520150272000001
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], cls.article_info_table_items)

        # create article_content_table
        cls.article_content_table_items = [
            {
                'article_id': 'testid000001',
                'body': 'testid000001 body',
                'title': 'testid000001 titile'
            },
            {
                'article_id': 'testid000003',
                'body': 'testid000003 body',
                'title': 'testid000003 titile'
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], cls.article_content_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = ArticlesShow(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        response = ArticlesShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'testid000001',
            'status': 'public',
            'title': 'testid000001 titile',
            'body': 'testid000001 body',
            'sort_key': 1520150272000000
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    def test_article_info_record_not_found(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000003'
            }
        }

        response = ArticlesShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 404)

    def test_article_content_record_not_found(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000002'
            }
        }

        response = ArticlesShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 404)

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        mock_lib = MagicMock()
        with patch('articles_show.DBUtil', mock_lib):
            ArticlesShow(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertEqual(args[1], 'testid000001')
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
            'pathParameters': {
                'article_id': 'A' * 13
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'pathParameters': {
                'article_id': 'A' * 11
            }
        }

        self.assert_bad_request(params)
