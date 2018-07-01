import os
import json
from unittest import TestCase
from me_comments_likes_create import MeCommentsLikesCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesCommentsCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        self.comment_liked_user_table = self.dynamodb.Table(os.environ['COMMENT_LIKED_USER_TABLE_NAME'])

        self.comment_items = [
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

        TestsUtil.create_table(self.dynamodb, os.environ['COMMENT_TABLE_NAME'], self.comment_items)

        comment_like_items = [
            {
                'comment_id': 'comment00002',
                'user_id': 'like_user_01',
                'created_at': 1520150272
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['COMMENT_LIKED_USER_TABLE_NAME'], comment_like_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        function = MeCommentsLikesCreate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'comment_id': 'comment00001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'like_user_01'
                    }
                }
            }
        }

        comment_before = self.comment_liked_user_table.scan()['Items']

        response = MeCommentsLikesCreate(params, {}, self.dynamodb).main()

        comment_after = self.comment_liked_user_table.scan()['Items']

        liked_user = self.comment_liked_user_table.get_item(
            Key={
                'comment_id': 'comment00001',
                'user_id': 'like_user_01'
            },
        ).get('Item')

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(comment_after) - len(comment_before), 1)
        self.assertIsNotNone(liked_user)

    def test_main_ok_already_liked_by_other_user(self):
        params = {
            'pathParameters': {
                'comment_id': 'comment00002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'like_user_02'
                    }
                }
            }
        }

        comment_before = self.comment_liked_user_table.scan()['Items']

        response = MeCommentsLikesCreate(params, {}, self.dynamodb).main()

        comment_after = self.comment_liked_user_table.scan()['Items']

        liked_user = self.comment_liked_user_table.get_item(
            Key={
                'comment_id': 'comment00002',
                'user_id': 'like_user_02'
            },
        ).get('Item')

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(comment_after) - len(comment_before), 1)
        self.assertIsNotNone(liked_user)

    def test_main_ok_already_liked_by_myself(self):
        params = {
            'pathParameters': {
                'comment_id': 'comment00002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'like_user_01'
                    }
                }
            }
        }

        comment_before = self.comment_liked_user_table.scan()['Items']

        response = MeCommentsLikesCreate(params, {}, self.dynamodb).main()

        comment_after = self.comment_liked_user_table.scan()['Items']

        liked_user = self.comment_liked_user_table.get_item(
            Key={
                'comment_id': 'comment00002',
                'user_id': 'like_user_02'
            },
        ).get('Item')

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body'])['message'], 'Already exists')
        self.assertEqual(len(comment_after) - len(comment_before), 0)
        self.assertIsNone(liked_user)

    def test_call_validate_comment_existence(self):
        params = {
            'pathParameters': {
                'comment_id': 'comment00008'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'like_user_01'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_comments_likes_create.DBUtil', mock_lib):
            MeCommentsLikesCreate(params, {}, self.dynamodb).main()
            args, _ = mock_lib.validate_comment_existence.call_args

            self.assertTrue(mock_lib.validate_comment_existence.called)
            self.assertEqual(args[1], 'comment00008')

    def test_validation_comment_id_max(self):
        params = {
            'pathParameters': {
                'comment_id': 'A' * 13
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'like_user_01'
                    }
                }
            }
        }
        self.assert_bad_request(params)
