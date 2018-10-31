import json
import os
from unittest import TestCase
from me_articles_drafts_update import MeArticlesDraftsUpdate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from text_sanitizer import TextSanitizer


class TestMeArticlesDraftsUpdate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

    def setUp(self):
        TestsUtil.delete_all_tables(self.dynamodb)

        self.article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        self.article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_info_items = [
            {
                'article_id': 'draftId00001',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0001',
                'user_id': 'test01',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'draftId00002',
                'user_id': 'test02',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'draftId00003',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000
            }
        ]

        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

        article_content_items = [
            {
                'article_id': 'draftId00001',
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

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesDraftsUpdate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
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

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        me_articles_drafts_update = MeArticlesDraftsUpdate(params, {}, self.dynamodb)

        response = me_articles_drafts_update.main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

        article_info_param_names = ['eye_catch_url', 'title', 'overview']
        article_content_param_names = ['title', 'body']

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_info_after[0]['user_id'])

        for key in article_info_param_names:
            self.assertEqual(json.loads(params['body'])[key], article_info_after[0][key])

        for key in article_content_param_names:
            self.assertEqual(json.loads(params['body'])[key], article_content_after[0][key])

    def test_main_ok_with_empty_string(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
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

        response = MeArticlesDraftsUpdate(params, {}, self.dynamodb).main()
        article_info = self.article_info_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        article_content = self.article_content_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['title'], None)
        self.assertEqual(article_info['overview'], None)
        self.assertEqual(article_content['title'], None)
        self.assertEqual(article_content['body'], None)

    def test_main_ok_article_content_not_exists(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00003'
            },
            'body': {
                'eye_catch_url': 'http://example.com/update',
                'title': 'A' * 255,
                'body': 'A' * 65535,
                'overview': 'A' * 100
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

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        me_articles_drafts_update = MeArticlesDraftsUpdate(params, {}, self.dynamodb)

        response = me_articles_drafts_update.main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 1)

        article_info_param_names = ['eye_catch_url', 'title', 'overview']
        article_content_param_names = ['title', 'body']

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_info_after[0]['user_id'])

        for key in article_info_param_names:
            target = [info for info in article_info_after if info['article_id'] == 'draftId00003'][0]
            self.assertEqual(json.loads(params['body'])[key], target[key])

        for key in article_content_param_names:
            target = [content for content in article_content_after if content['article_id'] == 'draftId00003'][0]
            self.assertEqual(json.loads(params['body'])[key], target[key])

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
        with patch('me_articles_drafts_update.DBUtil', mock_lib):
            MeArticlesDraftsUpdate(params, {}, self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
            self.assertEqual(kwargs['status'], 'draft')

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
                      "body": "<img src='a'><b>test</b><a href='bbb'>a</a><p>b</p><hr><div>c</div><u>d</u><i>e</i><br>"
                    },
                    "children": [
                      {
                        "type": "Text",
                        "payload": {
                          "body": "アップデートの"
                        }
                      },
                      {
                        "type": "Link",
                        "payload": {
                          "href": "https://example.com"
                        },
                        "children": [
                          {
                            "type": "Text",
                            "payload": {
                              "body": "テスト"
                            }
                          }
                        ]
                      },
                      {
                        "type": "Text",
                        "payload": {
                          "body": "です"
                        }
                      }
                    ]
                }]

        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
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
                        'cognito:username': 'test01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        me_articles_drafts_update = MeArticlesDraftsUpdate(params, {}, self.dynamodb)

        response = me_articles_drafts_update.main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

        article_info_param_names = ['eye_catch_url', 'title', 'overview']
        article_content_param_names = ['title', 'body']

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_info_after[0]['user_id'])

        for key in article_info_param_names:
            self.assertEqual(json.loads(params['body'])[key], article_info_after[0][key])

        for key in article_content_param_names:
            if key != 'body':
                self.assertEqual(json.loads(params['body'])[key], article_content_after[0][key])

        self.assertEqual(TextSanitizer.sanitize_article_object(body), article_content_after[0]['body'])
