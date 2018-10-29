import copy
import os
import json
from unittest import TestCase
from me_articles_comments_reply import MeArticlesCommentsReply
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesCommentsReply(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        os.environ['SALT_FOR_ARTICLE_ID'] = 'test_salt'

        self.article_info_table_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'articleuser01',
                'status': 'public',
                'title': 'testid000001 titile',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'articleuser02',
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
                'article_id': 'publicId0001',
                'user_id': 'commentuser01',
                'sort_key': 1520150271000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00002',
                'article_id': 'publicId0001',
                'user_id': 'commentuser02',
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser01',
                'sort_key': 1520150271000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00003',
                'article_id': 'publicId0001',
                'user_id': 'commentuser03',
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02',
                'sort_key': 1520150271000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00004',
                'article_id': 'publicId0001',
                'user_id': 'commentuser02',  # スレッド通知が二重に飛ばないことの検証用
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser01',
                'sort_key': 1520150271000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00005',
                'article_id': 'publicId0002',
                'user_id': 'commentuser01',
                'sort_key': 1520150271000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['COMMENT_TABLE_NAME'], self.comment_items)

        self.user_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        self.user_items = [
            {'user_id': 'articleuser01'},
            {'user_id': 'articleuser02'},
            {'user_id': 'commentuser01'},
            {'user_id': 'commentuser02'},
            {'user_id': 'commentuser03'},
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['USERS_TABLE_NAME'], self.user_items)

        self.notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['NOTIFICATION_TABLE_NAME'], [])

        self.unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'], [])

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesCommentsReply(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('me_articles_comments_reply.MeArticlesCommentsReply._MeArticlesCommentsReply__generate_comment_id',
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
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        comment_before = self.comment_table.scan()['Items']
        notification_before = self.notification_table.scan()['Items']
        unread_notification_manager_before = self.unread_notification_manager_table.scan()['Items']

        response = MeArticlesCommentsReply(params, {}, self.dynamodb).main()

        comment_after = self.comment_table.scan()['Items']
        notification_after = self.notification_table.scan()['Items']
        unread_notification_manager_after = self.unread_notification_manager_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['comment_id'], 'HOGEHOGEHOGE')
        self.assertEqual(len(comment_after) - len(comment_before), 1)
        self.assertEqual(len(notification_after) - len(notification_before), 4)
        self.assertEqual(len(unread_notification_manager_after) - len(unread_notification_manager_before), 4)

        comment = self.comment_table.get_item(Key={'comment_id': 'HOGEHOGEHOGE'}).get('Item')
        expected_comment = {
            'comment_id': 'HOGEHOGEHOGE',
            'text': 'A',
            'article_id': 'publicId0001',
            'user_id': 'test_user_id01',
            'parent_id': 'comment00001',
            'reply_user_id': 'commentuser02',
            'created_at': 1520150552,
            'sort_key': 1520150552000003
        }

        self.assertEqual(comment, expected_comment)

        reply_notification = self.notification_table.get_item(
            Key={'notification_id': 'reply-commentuser02-HOGEHOGEHOGE'}
        ).get('Item')

        comment_notification = self.notification_table.get_item(
            Key={'notification_id': 'comment-articleuser01-HOGEHOGEHOGE'}
        ).get('Item')

        thread_notification01 = self.notification_table.get_item(
            Key={'notification_id': 'thread-commentuser01-HOGEHOGEHOGE'}
        ).get('Item')

        thread_notification02 = self.notification_table.get_item(
            Key={'notification_id': 'thread-commentuser03-HOGEHOGEHOGE'}
        ).get('Item')

        expected_reply_notification = {
            'notification_id': 'reply-commentuser02-HOGEHOGEHOGE',
            'user_id': 'commentuser02',
            'article_id': self.article_info_table_items[0]['article_id'],
            'article_title': self.article_info_table_items[0]['title'],
            'acted_user_id': 'test_user_id01',
            'sort_key': 1520150552000003,
            'type': 'reply',
            'created_at': 1520150552
        }

        expected_comment_notification = {
            'notification_id': 'comment-articleuser01-HOGEHOGEHOGE',
            'user_id': 'articleuser01',
            'article_id': self.article_info_table_items[0]['article_id'],
            'article_title': self.article_info_table_items[0]['title'],
            'acted_user_id': 'test_user_id01',
            'sort_key': 1520150552000003,
            'type': 'comment',
            'created_at': 1520150552
        }

        expected_thread_notification01 = {
            'notification_id': 'thread-commentuser01-HOGEHOGEHOGE',
            'user_id': 'commentuser01',
            'article_id': self.article_info_table_items[0]['article_id'],
            'article_title': self.article_info_table_items[0]['title'],
            'acted_user_id': 'test_user_id01',
            'sort_key': 1520150552000003,
            'type': 'thread',
            'created_at': 1520150552
        }

        expected_thread_notification02 = {
            'notification_id': 'thread-commentuser03-HOGEHOGEHOGE',
            'user_id': 'commentuser03',
            'article_id': self.article_info_table_items[0]['article_id'],
            'article_title': self.article_info_table_items[0]['title'],
            'acted_user_id': 'test_user_id01',
            'sort_key': 1520150552000003,
            'type': 'thread',
            'created_at': 1520150552
        }

        self.assertEqual(reply_notification, expected_reply_notification)
        self.assertEqual(comment_notification, expected_comment_notification)
        self.assertEqual(thread_notification01, expected_thread_notification01)
        self.assertEqual(thread_notification02, expected_thread_notification02)

        for user_id in ['articleuser01', 'commentuser01', 'commentuser02', 'commentuser03']:
            self.assertEqual(
                self.unread_notification_manager_table.get_item(Key={'user_id': user_id}).get('Item'),
                {'user_id': user_id, 'unread': True}
            )

    '''
    記事投稿者が自らスレッドに返信するケース
    返信先への通知 + スレッド通知が行われる
    '''
    def test___create_comment_notifications_reply_article_user(self):
        params = {
            'article_id': 'publicId0001',
            'text': 'A',
            'parent_id': 'comment00001',
            'reply_user_id': 'commentuser01'
        }

        article_info = self.article_info_table_items[0]
        comment = {
            'comment_id': 'comment_id',
            'user_id': 'articleuser01'  # 記事投稿者が自らコメント
        }

        me_articles_comments_reply = MeArticlesCommentsReply(params, {}, self.dynamodb)
        me_articles_comments_reply.params = params

        notification_before = self.notification_table.scan()['Items']
        unread_notification_manager_before = self.unread_notification_manager_table.scan()['Items']

        me_articles_comments_reply._MeArticlesCommentsReply__create_comment_notifications(
            article_info, comment)

        notification_after = self.notification_table.scan()['Items']
        unread_notification_manager_after = self.unread_notification_manager_table.scan()['Items']

        self.assertEqual(len(notification_after) - len(notification_before), 3)
        self.assertEqual(len(unread_notification_manager_after) - len(unread_notification_manager_before), 3)

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'reply-commentuser01-comment_id'}).get('Item'))

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'thread-commentuser02-comment_id'}).get('Item'))

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'thread-commentuser03-comment_id'}).get('Item'))

    '''
    すでにスレッドにコメント済みのユーザーがスレッド内のコメントのユーザーに返信するケース
    返信先への通知 + スレッド通知 + 記事投稿者への通知が行われる
    スレッド通知の対象として、「返信したユーザー」「返信先のユーザー」が含まれないことを検証する
    '''
    def test___create_comment_notifications_reply_thread_user(self):
        params = {
            'article_id': 'publicId0001',
            'text': 'A',
            'parent_id': 'comment00001',
            'reply_user_id': 'commentuser02'
        }

        article_info = self.article_info_table_items[0]
        comment = {
            'comment_id': 'comment_id',
            'user_id': 'commentuser03'
        }

        me_articles_comments_reply = MeArticlesCommentsReply(params, {}, self.dynamodb)
        me_articles_comments_reply.params = params

        notification_before = self.notification_table.scan()['Items']
        unread_notification_manager_before = self.unread_notification_manager_table.scan()['Items']

        me_articles_comments_reply._MeArticlesCommentsReply__create_comment_notifications(
            article_info, comment)

        notification_after = self.notification_table.scan()['Items']
        unread_notification_manager_after = self.unread_notification_manager_table.scan()['Items']

        self.assertEqual(len(notification_after) - len(notification_before), 3)
        self.assertEqual(len(unread_notification_manager_after) - len(unread_notification_manager_before), 3)

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'reply-commentuser02-comment_id'}).get('Item'))

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'thread-commentuser01-comment_id'}).get('Item'))

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'comment-articleuser01-comment_id'}).get('Item'))

    '''
    コメントに対する初めての返信をテスト
    返信通知 + 記事投稿者への通知が行われる
    '''
    def test___create_comment_notifications_first_reply(self):
        params = {
            'article_id': 'publicId0002',
            'text': 'A',
            'parent_id': 'comment00005',
            'reply_user_id': 'commentuser01'
        }

        article_info = self.article_info_table_items[0]
        comment = {
            'comment_id': 'comment_id',
            'user_id': 'commentuser02'
        }

        me_articles_comments_reply = MeArticlesCommentsReply(params, {}, self.dynamodb)
        me_articles_comments_reply.params = params

        notification_before = self.notification_table.scan()['Items']
        unread_notification_manager_before = self.unread_notification_manager_table.scan()['Items']

        me_articles_comments_reply._MeArticlesCommentsReply__create_comment_notifications(
            article_info, comment)

        notification_after = self.notification_table.scan()['Items']
        unread_notification_manager_after = self.unread_notification_manager_table.scan()['Items']

        self.assertEqual(len(notification_after) - len(notification_before), 2)
        self.assertEqual(len(unread_notification_manager_after) - len(unread_notification_manager_before), 2)

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'reply-commentuser01-comment_id'}).get('Item'))

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'comment-articleuser01-comment_id'}).get('Item'))

    '''
    自分自身のコメントに対する返信の検証
    スレッド通知 + 記事投稿者への通知が行われる
    '''
    def test___create_comment_notifications_reply_own_comment(self):
        params = {
            'article_id': 'publicId0001',
            'text': 'A',
            'parent_id': 'comment00001',
            'reply_user_id': 'commentuser01'
        }

        article_info = self.article_info_table_items[0]
        comment = {
            'comment_id': 'comment_id',
            'user_id': 'commentuser01'
        }

        me_articles_comments_reply = MeArticlesCommentsReply(params, {}, self.dynamodb)
        me_articles_comments_reply.params = params

        notification_before = self.notification_table.scan()['Items']
        unread_notification_manager_before = self.unread_notification_manager_table.scan()['Items']

        me_articles_comments_reply._MeArticlesCommentsReply__create_comment_notifications(
            article_info, comment)

        notification_after = self.notification_table.scan()['Items']
        unread_notification_manager_after = self.unread_notification_manager_table.scan()['Items']

        self.assertEqual(len(notification_after) - len(notification_before), 3)
        self.assertEqual(len(unread_notification_manager_after) - len(unread_notification_manager_before), 3)

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'thread-commentuser02-comment_id'}).get('Item'))

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'thread-commentuser03-comment_id'}).get('Item'))

        self.assertIsNotNone(
            self.notification_table.get_item(
                Key={'notification_id': 'comment-articleuser01-comment_id'}).get('Item'))

    '''
    以下のprivateメソッドの基本的には振る舞いは上記のテストによって暗黙的に網羅テストされているので
    list.remove(args)時にValueErrorを無視する振る舞いのみテストを行う
    '''
    def test___get_thread_notification_targets_ignore_value_errors(self):
        user_id = 'comment10001'
        reply_user_id = 'articleuser01'
        parent_id = 'comment00001'
        me_articles_comments_reply = MeArticlesCommentsReply({}, {}, self.dynamodb)

        try:
            me_articles_comments_reply._MeArticlesCommentsReply__get_thread_notification_targets(
                user_id, reply_user_id, parent_id)
        except ValueError:
            self.fail('get_thread_notification_tagets() raised ValueError unexpectedly')

    def test_call_validate_comment_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'

            },
            'body': {
                'text': 'sample content',
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_comments_reply.DBUtil', mock_lib):
            MeArticlesCommentsReply(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args
            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertEqual(args[0], self.dynamodb)
            self.assertEqual(args[1], 'publicId0001')
            self.assertEqual(kwargs['status'], 'public')

            args, _ = mock_lib.validate_comment_existence.call_args
            self.assertTrue(mock_lib.validate_comment_existence.called)
            self.assertEqual(args[0], self.dynamodb)
            self.assertEqual(args[1], 'comment00001')

            args, _ = mock_lib.validate_user_existence.call_args
            self.assertTrue(mock_lib.validate_user_existence.called)
            self.assertEqual(args[0], self.dynamodb)
            self.assertEqual(args[1], 'commentuser02')

    @patch('me_articles_comments_reply.MeArticlesCommentsReply._MeArticlesCommentsReply__create_comment_notifications',
           MagicMock(side_effect=Exception()))
    def test_raise_exception_in_creating_notification(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': 'A',
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        response = MeArticlesCommentsReply(params, {}, self.dynamodb).main()

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
                        'cognito:username': 'test_user_id01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
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
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_body_required(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': 'AAA',
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        for param in ['text', 'parent_id', 'reply_user_id']:
            copy_params = copy.deepcopy(params)
            copy_params['body'][param] = None

            copy_params['body'] = json.dumps(copy_params['body'])

            self.assert_bad_request(copy_params)

        for param in ['text', 'parent_id', 'reply_user_id']:
            copy_params = copy.deepcopy(params)
            copy_params['body'][param] = ''

            copy_params['body'] = json.dumps(copy_params['body'])

            self.assert_bad_request(copy_params)

    def test_validation_empty_text(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': '',
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
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
                'parent_id': 'comment00001',
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_parent_id_max(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': 'A',
                'parent_id': 'A' * 13,
                'reply_user_id': 'commentuser02'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_reply_user_id_max(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'text': 'A',
                'parent_id': 'comment00001',
                'reply_user_id': 'A' * 31
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'comment_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)
