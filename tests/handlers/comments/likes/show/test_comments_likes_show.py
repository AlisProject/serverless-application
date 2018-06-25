import os
import json
from unittest import TestCase
from comments_likes_show import CommentsLikesShow
from tests_util import TestsUtil

class TestCommentsLikesShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        cls.comment_items = [
            {
                'comment_id': 'comment00001',
                'article_id': 'publicId0001',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00002',
                'article_id': 'publicId0001',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000001,
                'created_at': 1520150272,
                'text': 'コメントの内容2'
            }
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_TABLE_NAME'], cls.comment_items)

        comment_like_items = [
            {
                'comment_id': 'comment00001',
                'user_id': 'like_user_01',
                'created_at': 1520150272
            },
            {
                'comment_id': 'comment00001',
                'user_id': 'like_user_02',
                'created_at': 1520150272
            },
            {
                'comment_id': 'comment00001',
                'user_id': 'like_user_03',
                'created_at': 1520150272
            },
            {
                'comment_id': 'comment11111',
                'user_id': 'like_user_03',
                'created_at': 1520150272
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_LIKED_USER_TABLE_NAME'], comment_like_items)

    @classmethod
    def tearDownClass(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        response = CommentsLikesShow(params, {}, self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'comment_id': 'comment00001'
            }
        }

        response = CommentsLikesShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['count'], 3)

    def test_main_with_no_liked_comment(self):
        params = {
            'pathParameters': {
                'comment_id': 'comment00002'
            }
        }

        response = CommentsLikesShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['count'], 0)

    def test_main_with_comment_not_existed(self):
        params = {
            'pathParameters': {
                'comment_id': 'comment00003'
            }
        }

        response = CommentsLikesShow(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['count'], 0)

    def test_validation_comment_id_max(self):
        params = {
            'pathParameters': {
                'comment_id': 'A' * 13
            }
        }
        self.assert_bad_request(params)
