import json
import os
from unittest import TestCase
from me_articles_public_update import MeArticlesPublicUpdate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil


class TestMeArticlesPublicUpdate(TestCase):
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
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'test02',
                'title': 'sample_title2',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0003',
                'user_id': 'test03',
                'title': 'sample_title3',
                'status': 'public',
                'sort_key': 1520150272000000,
                'version': 200
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
            },
            {
                'article_id': 'publicId0003',
                'title': 'sample_title3',
                'body': [{
                    "type": "Paragraph",
                    "payload": {
                      "body": "test"
                    },
                    "children": []
                }],
                'version': 200
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

        article_content_edit_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'title': 'edit_title1',
                'body': 'edit_body1',
                'overview': 'edit_overview',
                'eye_catch_url': 'http://example.com/edit_eye_catch'
            },
            {
                'article_id': 'publicId0003',
                'user_id': 'test03',
                'title': 'edit_title3',
                'body': [{
                    "type": "Paragraph",
                    "payload": {
                      "body": "update"
                    },
                    "children": []
                }],
                'overview': 'edit_overview',
                'eye_catch_url': 'http://example.com/edit_eye_catch'
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'], article_content_edit_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesPublicUpdate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                'eye_catch_url': 'http://example.com/update',
                'title': 'update title',
                'body': '<p>update body</p>',
                'overview': 'update overview'
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
        response = MeArticlesPublicUpdate(params, {}, self.dynamodb).main()

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
                'eye_catch_url': 'http://example.com/update',
                'title': '',
                'body': '',
                'overview': ''
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
        response = MeArticlesPublicUpdate(params, {}, self.dynamodb).main()
        article_content_edit = self.article_content_edit_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        self.assertEqual(response['statusCode'], 200)

        expected_items = {
            'article_id': 'publicId0001',
            'eye_catch_url': 'http://example.com/update',
            'title': None,
            'body': None,
            'overview': None,
            'user_id': 'test01'
        }

        self.assertEqual(article_content_edit, expected_items)

    def test_main_ok_with_no_article_edit_content(self):
        prefix = 'http://'
        params = {
            'pathParameters': {
                'article_id': 'publicId0002'
            },
            'body': {
                'eye_catch_url': prefix + 'A' * (2048 - len(prefix)),
                'title': 'A' * 255,
                'body': 'A' * 65535,
                'overview': 'A' * 100
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
        response = MeArticlesPublicUpdate(params, {}, self.dynamodb).main()

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
                'article_id': 'draftId00001'
            },
            'body': {
                'eye_catch_url': 'http://example.com/update',
                'title': 'update title',
                'body': '<p>update body</p>',
                'overview': 'update overview'
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
        with patch('me_articles_public_update.DBUtil', mock_lib):
            MeArticlesPublicUpdate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
            self.assertEqual(kwargs['status'], 'public')

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
                'title': 'A' * 200
            },
            'pathParameters': {}
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_title_max(self):
        params = {
            'body': {
                'title': 'A' * 256
            },
            'pathParameters': {
                'article_id': 'A' * 12
            }
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

    def test_validation_eye_catch_url_max(self):
        prefix = 'http://'

        params = {
            'body': {
                'eye_catch_url': prefix + 'A' * (2049 - len(prefix))
            },
            'pathParameters': {
                'article_id': 'A' * 12
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_eye_catch_url_format(self):
        params = {
            'body': {
                'eye_catch_url': 'ALIS-invalid-url',
                'body': 'A' * 200
            },
            'pathParameters': {
                'article_id': 'A' * 12
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_overview_max(self):
        params = {
            'body': {
                'overview': 'A' * 101
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
                'overview': 'A' * 50
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

    def test_main_version200_ok(self):
        body = [{
                    "type": "Paragraph",
                    "payload": {
                      "body": "update"
                    },
                    "children": []
                }]

        params = {
            'pathParameters': {
                'article_id': 'publicId0003'
            },
            'body': {
                'eye_catch_url': 'http://example.com/update',
                'title': 'update title',
                'body': body,
                'overview': 'update overview',
                'version': 200
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        params['body'] = json.dumps(params['body'])
        response = MeArticlesPublicUpdate(params, {}, self.dynamodb).main()

        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), 0)

        article_content_edit = self.article_content_edit_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_content_edit['user_id'])

        for key, value in json.loads(params['body']).items():
            if key != 'body':
                self.assertEqual(value, article_content_edit[key])
            else:
                self.assertEqual(json.loads(params['body'])['body'], json.loads(article_content_edit['body']))
