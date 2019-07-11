import os
import json
import settings
from unittest import TestCase
from me_articles_content_edit_histories_index import MeArticlesContentEditHistoriesIndex
from tests_util import TestsUtil
from db_util import DBUtil
from unittest.mock import patch, MagicMock


class TestMeArticlesContentEditHistoriesIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        # create article_info_table_name
        items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test_user_id',
                'status': 'public',
                'version': 2,
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'test_user_id2',
                'status': 'public',
                'version': 2,
                'sort_key': 1520150272000003
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], items)

        # create article_content_edit_history_table
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'], [])
        # backup settings
        self.tmp_put_interval = settings.ARTICLE_HISTORY_PUT_INTERVAL

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def tearDown(self):
        # restore settings
        settings.ARTICLE_HISTORY_PUT_INTERVAL = self.tmp_put_interval

    def assert_bad_request(self, params):
        function = MeArticlesContentEditHistoriesIndex(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok_not_exists_content_edit_histories(self):
        params = {
            'queryStringParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesContentEditHistoriesIndex(params, {}, self.dynamodb).main()

        expected_items = []
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(expected_items, json.loads(response['body'])['Items'])

    def test_main_ok_exists_content_edit_histories_one(self):
        params = {
            'queryStringParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        # 1件作成
        test_body = 'test_body'
        DBUtil.put_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=params['requestContext']['authorizer']['claims']['cognito:username'],
            article_id=params['queryStringParameters']['article_id'],
            sanitized_body=test_body,
        )

        response = MeArticlesContentEditHistoriesIndex(params, {}, self.dynamodb).main()

        expected_item = {
            'user_id': params['requestContext']['authorizer']['claims']['cognito:username'],
            'article_edit_history_id': params['queryStringParameters']['article_id'] + '_' + '00',
            'article_id': params['queryStringParameters']['article_id'],
            'version': '00'
        }

        self.assertEqual(response['statusCode'], 200)
        actual_items = json.loads(response['body'])['Items']
        self.assertEqual(len(actual_items), 1)
        for key in expected_item.keys():
            self.assertEqual(expected_item[key], actual_items[0][key])

    def test_main_ok_exists_content_edit_histories_multiple(self):
        settings.ARTICLE_HISTORY_PUT_INTERVAL = 0
        params = {
            'queryStringParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        # 2件作成
        test_body = 'test_body'
        for i in range(2):
            DBUtil.put_article_content_edit_history(
                dynamodb=self.dynamodb,
                user_id=params['requestContext']['authorizer']['claims']['cognito:username'],
                article_id=params['queryStringParameters']['article_id'],
                sanitized_body=test_body,
            )

        response = MeArticlesContentEditHistoriesIndex(params, {}, self.dynamodb).main()

        # 降順
        expected_item = [
            {
                'user_id': params['requestContext']['authorizer']['claims']['cognito:username'],
                'article_edit_history_id': params['queryStringParameters']['article_id'] + '_' + '01',
                'article_id': params['queryStringParameters']['article_id'],
                'version': '01'
            },
            {
                'user_id': params['requestContext']['authorizer']['claims']['cognito:username'],
                'article_edit_history_id': params['queryStringParameters']['article_id'] + '_' + '00',
                'article_id': params['queryStringParameters']['article_id'],
                'version': '00'
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        actual_items = json.loads(response['body'])['Items']
        self.assertEqual(len(actual_items), 2)
        # 降順で取得できること
        for i in range(2):
            for key in expected_item[i].keys():
                self.assertEqual(expected_item[i][key], actual_items[i][key])

    def test_main_ng_another_user(self):
        params = {
            'queryStringParameters': {
                'article_id': 'publicId0002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesContentEditHistoriesIndex(params, {}, self.dynamodb).main()
        self.assertEqual(response['statusCode'], 403)

    def test_call_validate_article_existence(self):
        params = {
            'queryStringParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_content_edit_histories_index.DBUtil', mock_lib):
            MeArticlesContentEditHistoriesIndex(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertEqual(kwargs['user_id'], params['requestContext']['authorizer']['claims']['cognito:username'])
            self.assertEqual(kwargs['version'], 2)

    def test_validation_require_article_id(self):
        params = {
            'queryStringParameters': {
                'hoge': 'A' * 12
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 13
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 11
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)
