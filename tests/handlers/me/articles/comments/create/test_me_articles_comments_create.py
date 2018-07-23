import os
import json
from unittest import TestCase
from me_articles_comments_create import MeArticlesCommentsCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesCommentsCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        os.environ['SALT_FOR_ARTICLE_ID'] = 'test_salt'

        self.article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        self.article_info_table_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'article_user01',
                'status': 'public',
                'title': 'testid000001 titile',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'article_user02',
                'status': 'public',
                'title': 'testid000002 titile',
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], self.article_info_table_items)

        self.comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        self.comment_items = [
            {
                'comment_id': 'comment00001',
                'article_id': 'publicId0002',
                'user_id': 'comment_user_01',
                'sort_key': 1520150271000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['COMMENT_TABLE_NAME'], [])

        self.notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['NOTIFICATION_TABLE_NAME'], [])

        self.unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'], [])

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesCommentsCreate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('me_articles_comments_create.MeArticlesCommentsCreate._MeArticlesCommentsCreate__generate_comment_id',
           MagicMock(return_value='HOGEHOGEHOGE'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000003))
    @patch('time.time', MagicMock(return_value=1520150552.000003))
    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': 'A',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        comment_before = self.comment_table.scan()['Items']
        notification_before = self.notification_table.scan()['Items']
        unread_notification_manager_before = self.unread_notification_manager_table.scan()['Items']

        response = MeArticlesCommentsCreate(params, {}, self.dynamodb).main()

        comment_after = self.comment_table.scan()['Items']
        notification_after = self.notification_table.scan()['Items']
        unread_notification_manager_after = self.unread_notification_manager_table.scan()['Items']

        comment = self.comment_table.get_item(Key={'comment_id': 'HOGEHOGEHOGE'}).get('Item')
        notification = self.notification_table.get_item(
            Key={'notification_id': 'comment-article_user01-HOGEHOGEHOGE'}
        ).get('Item')

        unread_manager = self.unread_notification_manager_table.get_item(Key={'user_id': 'article_user01'}).get('Item')

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['comment_id'], 'HOGEHOGEHOGE')
        self.assertEqual(len(comment_after) - len(comment_before), 1)
        self.assertEqual(len(notification_after) - len(notification_before), 1)
        self.assertEqual(len(unread_notification_manager_after) - len(unread_notification_manager_before), 1)

        expected_comment = {
            'comment_id': 'HOGEHOGEHOGE',
            'text': 'A',
            'article_id': 'publicId0001',
            'user_id': 'test_user_id01',
            'created_at': 1520150552,
            'sort_key': 1520150552000003
        }

        expected_notification = {
            'notification_id': 'comment-article_user01-HOGEHOGEHOGE',
            'user_id': self.article_info_table_items[0]['user_id'],
            'article_id': self.article_info_table_items[0]['article_id'],
            'article_title': self.article_info_table_items[0]['title'],
            'acted_user_id': 'test_user_id01',
            'sort_key': 1520150552000003,
            'type': 'comment',
            'created_at': 1520150552
        }

        expected_unread_manager = {
            'user_id': self.article_info_table_items[0]['user_id'],
            'unread': True
        }

        self.assertEqual(comment, expected_comment)
        self.assertEqual(notification, expected_notification)
        self.assertEqual(unread_manager, expected_unread_manager)

    @patch('me_articles_comments_create.MeArticlesCommentsCreate._MeArticlesCommentsCreate__generate_comment_id',
           MagicMock(return_value='FUGAFUGAFUGA'))
    def test_main_ok_already_commented_by_myself(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            },
            'body': {
                'text': 'A' * 400,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        comment_before = self.comment_table.scan()['Items']

        response = MeArticlesCommentsCreate(params, {}, self.dynamodb).main()

        comment_after = self.comment_table.scan()['Items']

        comment = self.comment_table.get_item(Key={'comment_id': 'FUGAFUGAFUGA'}).get('Item')

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(comment_after) - len(comment_before), 1)
        self.assertIsNotNone(comment)

    def test_call_validate_comment_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0003'
            },
            'body': {
                'text': 'sample content',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_comments_create.DBUtil', mock_lib):
            MeArticlesCommentsCreate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertEqual(kwargs['status'], 'public')

    @patch('me_articles_comments_create.MeArticlesCommentsCreate._MeArticlesCommentsCreate__create_comment_notification',
           MagicMock(side_effect=Exception()))
    def test_raise_exception_in_creating_notification(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            },
            'body': {
                'text': 'sample content',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test05'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        response = MeArticlesCommentsCreate(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

    def test_validation_with_no_body(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'pathParameters': {
                'article_id': 'A' * 13
            },
            'body': {
                'text': 'sample content',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_no_text(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': None,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_empty_text(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': '',
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_text_max(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': 'A' * 401,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)
