import os
from tests_util import TestsUtil
from unittest import TestCase
from me_articles_like_create import MeArticlesLikeCreate
from unittest.mock import patch, MagicMock
from boto3.dynamodb.conditions import Key


class TestMeArticlesLikeCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        # create article_liked_user_table
        self.article_liked_user_table_items = [
            {
                'article_id': 'testid000000',
                'user_id': 'test01',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'user_id': 'test02',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'user_id': 'test03',
                'sort_key': 1520150272000002
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['ARTICLE_LIKED_USER_TABLE_NAME'],
            self.article_liked_user_table_items
        )

        # create article_info_table
        article_info_table_items = [
            {
                'article_id': 'testid000000',
                'title': 'title1',
                'status': 'public',
                'user_id': 'article_user_id_00',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'title': 'title2',
                'status': 'public',
                'user_id': 'article_user_id_01',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'title': 'title3',
                'status': 'draft',
                'user_id': 'article_user_id_01',
                'sort_key': 1520150272000002
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['ARTICLE_INFO_TABLE_NAME'],
            article_info_table_items
        )

        TestsUtil.create_table(self.dynamodb, os.environ['NOTIFICATION_TABLE_NAME'], [])

        self.unread_notification_manager_items = [
            {
                'user_id': 'article_user_id_00',
                'unread': False
            }
        ]
        TestsUtil.create_table(
            self.dynamodb, os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'],
            self.unread_notification_manager_items
        )

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        test_function = MeArticlesLikeCreate(params, {}, self.dynamodb)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('time.time', MagicMock(return_value=1520150272.000003))
    def test_main_ok_exist_article_id(self):
        params = {
            'pathParameters': {
                'article_id': self.article_liked_user_table_items[0]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test05'
                    }
                }
            }
        }

        article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        article_liked_user_before = article_liked_user_table.scan()['Items']
        unread_notification_manager_before = unread_notification_manager_table.scan()['Items']

        article_liked_user = MeArticlesLikeCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        article_liked_user_after = article_liked_user_table.scan()['Items']
        unread_notification_manager_after = unread_notification_manager_table.scan()['Items']

        target_article_id = params['pathParameters']['article_id']
        target_user_id = params['requestContext']['authorizer']['claims']['cognito:username']

        article_liked_user = self.get_article_liked_user(target_article_id, target_user_id)

        expected_items = {
            'article_id': target_article_id,
            'user_id': target_user_id,
            'article_user_id': 'article_user_id_00',
            'created_at': 1520150272,
            'target_date': '2018-03-04',
            'sort_key': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_liked_user_after), len(article_liked_user_before) + 1)
        self.assertEqual(len(unread_notification_manager_after), len(unread_notification_manager_before))
        article_liked_user_param_names = ['article_id', 'user_id', 'article_user_id', 'created_at', 'target_date', 'sort_key']
        for key in article_liked_user_param_names:
            self.assertEqual(expected_items[key], article_liked_user[key])

        unread_notification_manager = unread_notification_manager_table.get_item(
            Key={'user_id': 'article_user_id_00'}
        ).get('Item')
        self.assertEqual(unread_notification_manager['unread'], True)

    @patch('time.time', MagicMock(return_value=1520150272.000003))
    def test_create_notification_and_unread_notification_manager(self):
        params = {
            'pathParameters': {
                'article_id': self.article_liked_user_table_items[1]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test06'
                    }
                }
            }
        }

        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        notification_before = notification_table.scan()['Items']
        unread_notification_manager_before = unread_notification_manager_table.scan()['Items']

        article_liked_user = MeArticlesLikeCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_liked_user.main()

        notification_after = notification_table.scan()['Items']
        unread_notification_manager_after = unread_notification_manager_table.scan()['Items']

        expected_notifications = [
            {
                'user_id': 'article_user_id_01',
                'sort_key': 1520150272000003,
                'article_id': 'testid000001',
                'article_title': 'title2',
                'type': 'like',
                'acted_user_id': 'test06',
                'created_at': 1520150272
            }
        ]

        unread_notification_manager = unread_notification_manager_table.get_item(
            Key={'user_id': 'article_user_id_01'}
        ).get('Item')

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(notification_after, expected_notifications)
        self.assertEqual(len(notification_after), len(notification_before) + 1)
        self.assertEqual(unread_notification_manager['unread'], True)
        self.assertEqual(len(unread_notification_manager_after), len(unread_notification_manager_before) + 1)

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test05'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_like_create.DBUtil', mock_lib):
            MeArticlesLikeCreate(event=params, context={}, dynamodb=self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertEqual(kwargs['status'], 'public')

    def test_main_ng_exist_user_id(self):
        params = {
            'pathParameters': {
                'article_id': self.article_liked_user_table_items[0]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_liked_user_table_items[0]['user_id']
                    }
                }
            }
        }

        response = MeArticlesLikeCreate(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 13
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 11
            }
        }

        self.assert_bad_request(params)

    def get_article_liked_user(self, article_id, user_id):
        query_params = {
            'KeyConditionExpression': Key('article_id').eq(article_id) & Key('user_id').eq(user_id)
        }
        article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
        return article_liked_user_table.query(**query_params)['Items'][0]
