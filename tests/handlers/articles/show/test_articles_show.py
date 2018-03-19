from unittest import TestCase
from articles_show import ArticlesShow
from unittest.mock import patch, MagicMock
import yaml
import os
import boto3
import json


class TestArticlesShow(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    target_tables = ['ArticleInfo', 'ArticleContent']

    @classmethod
    def setUpClass(cls):
        os.environ['ARTICLE_INFO_TABLE_NAME'] = 'ArticleInfo'
        os.environ['ARTICLE_CONTENT_TABLE_NAME'] = 'ArticleContent'

        f = open("./database.yaml", "r+")
        template = yaml.load(f)
        f.close()

        for table_name in cls.target_tables:
            create_params = {'TableName': table_name}
            create_params.update(template['Resources'][table_name]['Properties'])

            cls.dynamodb.create_table(**create_params)

        article_info_table = cls.dynamodb.Table('ArticleInfo')
        items = [
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

        for item in items:
            article_info_table.put_item(Item=item)

        article_content_table = cls.dynamodb.Table('ArticleContent')
        items = [
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

        for item in items:
            article_content_table.put_item(Item=item)

    @classmethod
    def tearDownClass(cls):
        for table_name in cls.target_tables:
            cls.dynamodb.Table(table_name).delete()

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

    @patch('articles_show.validate', MagicMock(side_effect=Exception()))
    def test_main_ng_with_internal_server_error(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        response = ArticlesShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 500)

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
