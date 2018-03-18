from unittest import TestCase
from articles_alis_tokens_show import ArticlesAlisTokensShow
from unittest.mock import patch, MagicMock
import yaml
import os
import boto3
import json


class TestArticlesAlisTokensShow(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    target_tables = ['ArticleAlisToken', 'ArticleEvaluatedManage']

    @classmethod
    def setUpClass(cls):
        os.environ['ARTICLE_ALIS_TOKEN_TABLE_NAME'] = 'ArticleAlisToken'
        os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'] = 'ArticleEvaluatedManage'

        f = open("./database.yaml", "r+")
        template = yaml.load(f)
        f.close()

        for table_name in cls.target_tables:
            create_params = {'TableName': table_name}
            create_params.update(template['Resources'][table_name]['Properties'])

            cls.dynamodb.create_table(**create_params)

        article_evaluated_manage_table = cls.dynamodb.Table('ArticleEvaluatedManage')
        article_evaluated_manage_table.put_item(Item={'active_evaluated_at': 1520150272000000})

        article_alis_token_table = cls.dynamodb.Table('ArticleAlisToken')
        article_alis_tokens = [
            {
                'article_id': 'testid000001',
                'alis_token': 100,
                'evaluated_at': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'alis_token': 50,
                'evaluated_at': 1520150272000000
            },
            {
                'article_id': 'testid000003',
                'alis_token': 150,
                'evaluated_at': 1520150572000000
            },
            {
                'article_id': 'testid000001',
                'alis_token': 80,
                'evaluated_at': 1520150572000000
            }
        ]

        for article_alis_token in article_alis_tokens:
            article_alis_token_table.put_item(Item=article_alis_token)

    @classmethod
    def tearDownClass(cls):
        for table_name in cls.target_tables:
            cls.dynamodb.Table(table_name).delete()

    def assert_bad_request(self, params):
        function = ArticlesAlisTokensShow(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        response = ArticlesAlisTokensShow(params, {}, self.dynamodb).main()

        expected_item = {
            'article_id': 'testid000001',
            'alis_token': 100,
            'evaluated_at': 1520150272000000
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)

    @patch('articles_alis_tokens_show.validate', MagicMock(side_effect=Exception()))
    def test_main_ng_with_internal_server_error(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        response = ArticlesAlisTokensShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 500)

    def test_record_not_found(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000003'
            }
        }

        response = ArticlesAlisTokensShow(params, {}, self.dynamodb).main()

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
