import json
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from tests_util import TestsUtil
from articles_supporters_index import ArticlesSupportersIndex


class TestArticlesSupportersIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.user_items = [
            {
                'user_id': 'user00001',
                'user_display_name': 'user00001',
                'self_introduction': 'self_introduction00001',
                'icon_image_url': 'http://example.com',
            },
            {
                'user_id': 'user00002',
                'user_display_name': 'user00002',
                'self_introduction': 'self_introduction00002',
                'icon_image_url': 'http://example.com',
            },
            {
                'user_id': 'user00003',
                'user_display_name': 'user00003',
                'self_introduction': 'self_introduction00003',
                'icon_image_url': 'http://example.com',
            }
            ,
            {'user_id': 'user00004'},
            {'user_id': 'user00005'}
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['USERS_TABLE_NAME'], self.user_items)

        # create article_info_table
        self.article_info_table_items = [
            {
                'article_id': 'testid000001',
                'user_id': 'testuser001',
                'status': 'public',
                'title': 'testid000001 titile',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'user_id': 'testuser002',
                'status': 'public',
                'title': 'testid000002 titile',
                'sort_key': 1520150272000001
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], self.article_info_table_items)

        self.tip_items = [
            {
                "article_id": "testid000001",
                "article_title": "testid000001 titile",
                "created_at": 1536184800,
                "sort_key": 1536123933198548,
                "tip_value": 10000000000000000000,  # 10 ALIS
                "to_user_id": "testuser001",
                "transaction": "0xfc2f63e2ef0323c0746d60807212ea87e3e6f56767b62f2d6ed6f72bfe9ab533",
                "user_id": "user00001"
            },
            {
                "article_id": "testid000001",
                "article_title": "testid000001 titile",
                "created_at": 1536184800,
                "sort_key": 1536123933198549,
                "tip_value": 10000000000000000000,  # 10 ALIS
                "to_user_id": "testuser001",
                "transaction": "0xfc2f63e2ef0323c0746d60807212ea87e3e6f56767b62f2d6ed6f72bfe9ab533",
                "user_id": "user00001"
            },
            {
                "article_id": "testid000001",
                "article_title": "testid000001 titile",
                "created_at": 1536184800,
                "sort_key": 1536123933198550,
                "tip_value": 100000000000000000000,  # 100 ALIS
                "to_user_id": "testuser001",
                "transaction": "0xfc2f63e2ef0323c0746d60807212ea87e3e6f56767b62f2d6ed6f72bfe9ab533",
                "user_id": "user00002"
            },
            {
                "article_id": "8n9oVG611111",
                "article_title": "テスト記事タイトル2",
                "created_at": 1536184800,
                "sort_key": 1536123933198549,
                "tip_value": 100000000000000000000,  # 100 ALIS
                "to_user_id": "testuser004",
                "transaction": "0xfc2f63e2ef0323c0746d60807212ea87e3e6f56767b62f2d6ed6f71111111111",
                "user_id": "testuser003"
            },
            {
                # uncompletedが存在しないデータは対象外
                "article_id": "8n9oVG622222",
                "article_title": "対象外記事タイトル",
                "created_at": 1536184800,
                "sort_key": 1536123933198550,
                "tip_value": 100000000000000000000,  # 100 ALIS
                "to_user_id": "testuser006",
                "transaction": "0xfc2f63e2ef0323c0746d60807212ea87e3e6f56767b62f2d6ed6f7222222222",
                "user_id": "testuser005"
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['SUCCEEDED_TIP_TABLE_NAME'], self.tip_items)

    def tearDown(self):
        pass

    def assert_bad_request(self, params):
        function = ArticlesSupportersIndex(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        response = ArticlesSupportersIndex(params, {}, dynamodb=self.dynamodb).main()

        expected = [
            {
                'user_id': 'user00002',
                'user_display_name': 'user00002',
                'icon_image_url': 'http://example.com',
                'sum_tip_value': 100000000000000000000  # 100 ALIS
            },
            {
                'user_id': 'user00001',
                'user_display_name': 'user00001',
                'icon_image_url': 'http://example.com',
                'sum_tip_value': 20000000000000000000  # 20 ALIS
            }
        ]

        self.assertEqual(expected, json.loads(response['body'])['Items'])

    def test_main_ok_over_100(self):
        user_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        with user_table.batch_writer() as batch:
            for i in range(100):
                batch.put_item(Item={
                    'user_id': 'batch_user' + str(i),
                    'user_display_name': 'user',
                    'self_introduction': 'self_introduction',
                    'icon_image_url': 'http://example.com'
                })

        succeeded_tip_table = self.dynamodb.Table(os.environ['SUCCEEDED_TIP_TABLE_NAME'])
        with succeeded_tip_table.batch_writer() as batch:
            for i in range(100):

                batch.put_item(Item={
                    'article_id': 'testid000001',
                    'article_title': 'testid000001',
                    'created_at': 1536184800,
                    'sort_key': 1536123933198600 + i,
                    'tip_value': 10000000000000000000,  # 10 ALIS
                    'to_user_id': 'testuser001',
                    'transaction': '0xfc2f63e2ef0323c0746d60807212ea87e3e6f56767b62f2d6ed6f72bfe9ab533',
                    'user_id': 'batch_user' + str(i)
                })

        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        response = ArticlesSupportersIndex(params, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(102, len(json.loads(response['body'])['Items']))


    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000001'
            }
        }

        mock_lib = MagicMock()
        with patch('articles_supporters_index.DBUtil', mock_lib):
            ArticlesSupportersIndex(params, {}, self.dynamodb).main()
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
