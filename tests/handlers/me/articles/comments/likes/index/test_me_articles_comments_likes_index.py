import os
import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from me_articles_comments_likes_index import MeArticlesCommentsLikesIndex
from tests_util import TestsUtil


class TestMeArticlesCommentsLikesIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

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
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

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
            },
            {
                'comment_id': 'comment00003',
                'article_id': 'publicId0001',
                'user_id': 'test_user_02',
                'sort_key': 1520150272000002,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00004',
                'article_id': 'publicId0002',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000004,
                'created_at': 1520150272,
                'text': 'コメントの内容4'
            },
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_TABLE_NAME'], cls.comment_items)

        comment_like_items = [
            {
                'comment_id': 'comment00001',
                'user_id': 'like_user_01',
                'article_id': 'publicId0001',
                'created_at': 1520150272
            },
            {
                'comment_id': 'comment00001',
                'user_id': 'like_user_02',
                'article_id': 'publicId0001',
                'created_at': 1520150272
            },
            {
                'comment_id': 'comment00002',
                'user_id': 'like_user_02',
                'article_id': 'publicId0001',
                'created_at': 1520150272
            },
            {
                'comment_id': 'comment00003',
                'user_id': 'like_user_01',
                'article_id': 'publicId0001',
                'created_at': 1520150272
            },
            {
                'comment_id': 'comment00004',
                'user_id': 'like_user_01',
                'article_id': 'publicId0002',
                'created_at': 1520150272
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_LIKED_USER_TABLE_NAME'], comment_like_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        response = MeArticlesCommentsLikesIndex(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'like_user_01'
                    }
                }
            }
        }

        response = MeArticlesCommentsLikesIndex(event=params, context={}, dynamodb=self.dynamodb).main()

        expected_items = [self.comment_items[0]['comment_id'], self.comment_items[2]['comment_id']]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(sorted(json.loads(response['body'])['comment_ids']), sorted(expected_items))

    def test_main_with_no_likes(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id02'
                    }
                }
            }
        }

        response = MeArticlesCommentsLikesIndex(event=params, context={}, dynamodb=self.dynamodb).main()

        expected_items = []

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['comment_ids'], expected_items)

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_comments_likes_index.DBUtil', mock_lib):
            MeArticlesCommentsLikesIndex(event=params, context={}, dynamodb=self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertEqual(kwargs['status'], 'public')

    def test_validation_article_id_none(self):
        params = {
            'pathParameters': {
                'article_id': None
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'pathParameters': {
                'article_id': 'A' * 13
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)
