from unittest import TestCase
from me_articles_drafts_create import MeArticlesDraftsCreate
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from tests_util import TestsUtil
from text_sanitizer import TextSanitizer
import os
import json


class TestMeArticlesDraftsCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)
        os.environ['SALT_FOR_ARTICLE_ID'] = 'test_salt'

    def setUp(self):
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], [])
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], [])
        self.article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        self.article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesDraftsCreate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch("me_articles_drafts_create.MeArticlesDraftsCreate._MeArticlesDraftsCreate__generate_article_id",
           MagicMock(return_value='HOGEHOGEHOGE'))
    def test_main_ok(self):
        params = {
            'body': {
                "eye_catch_url": "http://example.com",
                "title": "sample title",
                "body": "<p>sample body</p>",
                "overview": " "
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

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        me_articles_drafts_create = MeArticlesDraftsCreate(params, {}, self.dynamodb)

        response = me_articles_drafts_create.main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(json.loads(response['body']), {'article_id': 'HOGEHOGEHOGE'})

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_info_after) - len(article_info_before), 1)
        self.assertEqual(len(article_content_after) - len(article_content_before), 1)

        article_info_param_names = ['eye_catch_url', 'title', 'overview']
        article_content_param_names = ['title', 'body']

        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_info_after[0]['user_id'])

        for key in article_info_param_names:
            self.assertEqual(json.loads(params['body'])[key], article_info_after[0][key])

        for key in article_content_param_names:
            self.assertEqual(json.loads(params['body'])[key], article_content_after[0][key])

    @patch("me_articles_drafts_create.MeArticlesDraftsCreate._MeArticlesDraftsCreate__generate_article_id",
           MagicMock(return_value='HOGEHOGEHOGE'))
    def test_main_ok_with_empty_string(self):
        params = {
            'body': {
                'eye_catch_url': 'http://example.com',
                'title': '',
                'body': '',
                'overview': ''
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

        params['body'] = json.dumps(params['body'])

        response = MeArticlesDraftsCreate(params, {}, self.dynamodb).main()
        article_info = self.article_info_table.get_item(Key={'article_id': 'HOGEHOGEHOGE'})['Item']
        article_content = self.article_content_table.get_item(Key={'article_id': 'HOGEHOGEHOGE'})['Item']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['title'], None)
        self.assertEqual(article_info['overview'], None)
        self.assertEqual(article_content['title'], None)
        self.assertEqual(article_content['body'], None)

    @patch("me_articles_drafts_create.validate", MagicMock(side_effect=Exception()))
    def test_main_with_internal_server_error_on_create_article_info(self):
        params = {
            'body': {
                'eye_catch_url': 'http://example.com',
                'title': 'sample title',
                'body': '<p>sample body</p>',
                'overview': 'sample body'
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

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = MeArticlesDraftsCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body'])['message'], 'Internal server error')
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch('me_articles_drafts_create.MeArticlesDraftsCreate._MeArticlesDraftsCreate__generate_article_id',
           MagicMock(return_value='HOGEHOGEHOGE'))
    @patch('me_articles_drafts_create.MeArticlesDraftsCreate._MeArticlesDraftsCreate__create_article_content',
           MagicMock(side_effect=Exception()))
    def test_main_with_error_on_create_article_content(self):
        params = {
            'body': {
                'eye_catch_url': 'http://example.com',
                'title': 'sample title',
                'body': '<p>sample body</p>',
                'overview': 'sample body'
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

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = MeArticlesDraftsCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'article_id': 'HOGEHOGEHOGE'})
        self.assertEqual(len(article_info_after) - len(article_info_before), 1)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch('me_articles_drafts_create.MeArticlesDraftsCreate._MeArticlesDraftsCreate__generate_article_id',
           MagicMock(return_value='HOGEHOGEHOGE'))
    def test_main_with_article_id_already_exsits(self):
        self.article_info_table.put_item(
            Item={
                'article_id': 'HOGEHOGEHOGE',
                'user_id': 'USER_ID',
                'status': 'draft',
                'sort_key': 1521120784000001,
            }
        )

        params = {
            'body': {
                'eye_catch_url': 'http://example.com',
                'title': 'sample title',
                'body': '<p>sample body</p>',
                'overview': 'sample body'
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

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = MeArticlesDraftsCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), {'message': 'Already exists'})
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch('me_articles_drafts_create.MeArticlesDraftsCreate._MeArticlesDraftsCreate__generate_article_id',
           MagicMock(return_value='HOGEHOGEHOGE'))
    def test_create_article_content_with_article_id_already_exsits(self):
        self.article_content_table.put_item(
            Item={
                'article_id': 'HOGEHOGEHOGE',
                'title': 'test_title',
                'body': 'test_body'
            }
        )

        article_id = 'HOGEHOGEHOGE'
        params = {
            'title': 'sample title',
            'body': '<p>sample body</p>'
        }

        article_draft_create = MeArticlesDraftsCreate({}, {}, self.dynamodb)

        article_content_before = self.article_content_table.scan()['Items']

        with self.assertRaises(ClientError):
            article_draft_create._MeArticlesDraftsCreate__create_article_content(params, article_id)

        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    def test_generate_article_id(self):
        me_articles_drafts_create = MeArticlesDraftsCreate({}, {}, self.dynamodb)

        target_sort_key1 = 1521120784000001
        target_sort_key2 = 1521120784000002

        hashid1 = me_articles_drafts_create._MeArticlesDraftsCreate__generate_article_id(target_sort_key1)
        hashid2 = me_articles_drafts_create._MeArticlesDraftsCreate__generate_article_id(target_sort_key2)

        self.assertNotEqual(hashid1, hashid2)
        self.assertEqual(len(hashid1), 12)
        self.assertEqual(len(hashid2), 12)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_title_max(self):
        params = {
            'body': {
                'title': 'A' * 256
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_body_max(self):
        params = {
            'body': {
                'body': 'A' * 65536
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_eye_catch_url_max(self):
        prefix = 'http://'

        params = {
            'body': {
                'eye_catch_url': prefix + 'A' * (2049 - len(prefix))
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_eye_catch_url_format(self):
        params = {
            'body': {
                'eye_catch_url': 'ALIS-invalid-url',
                'body': 'A' * 200
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_overview_max(self):
        params = {
            'body': {
                'overview': 'A' * 101
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    @patch("me_articles_drafts_create.MeArticlesDraftsCreate._MeArticlesDraftsCreate__generate_article_id",
           MagicMock(return_value='HOGEHOGEHOGE'))
    def test_main_ok_with_editor_version2(self):
        body = [{
                    "type": "Paragraph",
                    "payload": {
                      "body": "<img src='a'><b>test</b><a href='bbb'>a</a><p>b</p><hr><div>c</div><u>d</u><i>e</i><br>"
                    },
                    "children": [
                      {
                        "type": "Text",
                        "payload": {
                          "body": "<b>詳細は</b>"
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
                              "body": "こちら"
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
            'body': {
                'eye_catch_url': 'http://example.com',
                'title': 'test',
                'body': body,
                'overview': '',
                'version': 200
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

        params['body'] = json.dumps(params['body'])

        response = MeArticlesDraftsCreate(params, {}, self.dynamodb).main()
        article_info = self.article_info_table.get_item(Key={'article_id': 'HOGEHOGEHOGE'})['Item']
        article_content = self.article_content_table.get_item(Key={'article_id': 'HOGEHOGEHOGE'})['Item']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['title'], 'test')
        self.assertEqual(article_info['overview'], None)
        self.assertEqual(article_content['title'], 'test')
        self.assertEqual(article_content['body'], TextSanitizer.sanitize_article_object(body))
