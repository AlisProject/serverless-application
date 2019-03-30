from unittest import TestCase
from articles_price_show import ArticlesPriceShow
from tests_util import TestsUtil
from unittest.mock import patch, MagicMock
import os
import json


class TestArticlesPriceShow(TestCase):
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
                'price': 100,
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

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = ArticlesPriceShow(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        response = ArticlesPriceShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'testid000001',
            'price': 100,
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    def test_record_is_not_paid_article(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000002'
            }
        }

        response = ArticlesPriceShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 404)

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        mock_lib = MagicMock()
        with patch('articles_price_show.DBUtil', mock_lib):
            ArticlesPriceShow(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertEqual(args[1], 'testid000001')
            self.assertEqual(kwargs['status'], 'public')
            self.assertEqual(kwargs['is_purchased'], True)

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
