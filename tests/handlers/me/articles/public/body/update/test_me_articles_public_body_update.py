import json
import os
from unittest import TestCase
from me_articles_public_body_update import MeArticlesPublicBodyUpdate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesPublicBodyUpdate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

    def setUp(self):
        TestsUtil.delete_all_tables(self.dynamodb)

        self.article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])

        article_info_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'title': 'sample_title1',
                'status': 'public',
                'sort_key': 1520150272000000,
                'version': 2
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'test02',
                'title': 'sample_title2',
                'status': 'public',
                'sort_key': 1520150272000000,
                'version': 2
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_content_items = [
            {
                'article_id': 'publicId0001',
                'title': 'sample_title1',
                'body': 'sample_body1'
            },
            {
                'article_id': 'publicId0002',
                'title': 'sample_title2',
                'body': 'sample_body2'
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

        self.article_content_edit_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'title': 'edit_title1',
                'body': 'edit_body1',
                'overview': 'edit_overview',
                'eye_catch_url': 'http://example.com/edit_eye_catch'
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'],
                               self.article_content_edit_items)

        # create article_content_edit_history_table
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'], [])

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        me_articles_public_body_update = MeArticlesPublicBodyUpdate(params, {}, self.dynamodb)
        response = me_articles_public_body_update.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'body': '<p>update body</p>'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        params['body'] = json.dumps(params['body'])
        response = MeArticlesPublicBodyUpdate(params, {}, self.dynamodb).main()

        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), 0)

        article_content_edit = self.article_content_edit_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_content_edit['user_id'])

        for key, value in json.loads(params['body']).items():
            self.assertEqual(value, article_content_edit[key])

    def test_main_ok_with_empty_string(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'body': ''
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])
        response = MeArticlesPublicBodyUpdate(params, {}, self.dynamodb).main()
        article_content_edit = self.article_content_edit_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        self.assertEqual(response['statusCode'], 200)

        expected_items = {
            'article_id': self.article_content_edit_items[0].get('article_id'),
            'eye_catch_url': self.article_content_edit_items[0].get('eye_catch_url'),
            'title': self.article_content_edit_items[0].get('title'),
            'body': None,
            'overview': self.article_content_edit_items[0].get('overview'),
            'user_id': self.article_content_edit_items[0].get('user_id'),
        }

        self.assertEqual(article_content_edit, expected_items)

    def test_main_ok_with_no_article_edit_content(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            },
            'body': {
                'body': 'A' * 65535
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test02',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        params['body'] = json.dumps(params['body'])
        response = MeArticlesPublicBodyUpdate(params, {}, self.dynamodb).main()

        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), 1)

        article_content_edit = self.article_content_edit_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_content_edit['user_id'])

        for key, value in json.loads(params['body']).items():
            self.assertEqual(value, article_content_edit[key])

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'body': '<p>update body</p>'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_public_body_update.DBUtil', mock_lib):
            MeArticlesPublicBodyUpdate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
            self.assertEqual(kwargs['status'], 'public')
            self.assertEqual(kwargs['version'], 2)

    def test_call_sanitize_article_body_v2(self):
        body_str = '<p>update body</p>'
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'body': body_str
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_public_body_update.TextSanitizer', mock_lib):
            MeArticlesPublicBodyUpdate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.sanitize_article_body_v2.call_args
            self.assertTrue(mock_lib.sanitize_article_body_v2.called)
            self.assertEqual(args[0], body_str)

    def test_call_create_article_content_edit_history(self):
        body_str = '<p>update body</p>'
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'body': body_str
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_public_body_update.DBUtil', mock_lib):
            MeArticlesPublicBodyUpdate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.put_article_content_edit_history.call_args
            self.assertTrue(mock_lib.put_article_content_edit_history.called)
            self.assertTrue(kwargs['dynamodb'] is not None)
            self.assertEqual('test01', kwargs['user_id'])
            self.assertEqual('publicId0001', kwargs['article_id'])
            self.assertEqual(body_str, kwargs['sanitized_body'])

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_with_no_body_params(self):
        params = {
            'body': {},
            'pathParameters': {
                'article_id': 'A' * 12
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_with_no_path_params(self):
        params = {
            'body': {
                'body': 'A' * 200
            },
            'pathParameters': {}
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_body_max(self):
        params = {
            'body': {
                'body': 'A' * 65536
            },
            'pathParameters': {
                'article_id': 'A' * 12
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'body': {
                'body': 'A' * 50
            },
            'pathParameters': {
                'article_id': 'A' * 13
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'body': {
                'overview': 'A' * 50
            },
            'pathParameters': {
                'article_id': 'A' * 11
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)
