from unittest import TestCase
from articles_draft_create import ArticlesDraftCreate
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import yaml
import os
import boto3
import json


class TestArticlesDraftCreate(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    target_tables = ['ArticleInfo', 'ArticleContent']

    @classmethod
    def setUpClass(cls):
        os.environ['ARTICLE_INFO_TABLE_NAME'] = 'ArticleInfo'
        os.environ['ARTICLE_CONTENT_TABLE_NAME'] = 'ArticleContent'
        os.environ['SALT_FOR_ARTICLE_ID'] = 'test_salt'

    def setUp(self):
        f = open("./database.yaml", "r+")
        template = yaml.load(f)
        f.close()

        for table_name in self.target_tables:
            create_params = {'TableName': table_name}
            create_params.update(template['Resources'][table_name]['Properties'])

            self.dynamodb.create_table(**create_params)

        self.article_info_table = self.dynamodb.Table('ArticleInfo')
        self.article_content_table = self.dynamodb.Table('ArticleContent')

    def tearDown(self):
        for table_name in self.target_tables:
            self.dynamodb.Table(table_name).delete()

    def assert_bad_request(self, params):
        function = ArticlesDraftCreate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch("articles_draft_create.ArticlesDraftCreate._ArticlesDraftCreate__generate_article_id",
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
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        articles_draft_create = ArticlesDraftCreate(params, {}, self.dynamodb)

        response = articles_draft_create.main()

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

    @patch("articles_draft_create.validate", MagicMock(side_effect=Exception()))
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
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = ArticlesDraftCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body'])['message'], 'Internal server error')
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch('articles_draft_create.ArticlesDraftCreate._ArticlesDraftCreate__generate_article_id',
           MagicMock(return_value='HOGEHOGEHOGE'))
    @patch('articles_draft_create.ArticlesDraftCreate._ArticlesDraftCreate__create_article_content',
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
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = ArticlesDraftCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'article_id': 'HOGEHOGEHOGE'})
        self.assertEqual(len(article_info_after) - len(article_info_before), 1)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch('articles_draft_create.ArticlesDraftCreate._ArticlesDraftCreate__generate_article_id',
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
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = ArticlesDraftCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), {'message': 'Already exists'})
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch('articles_draft_create.ArticlesDraftCreate._ArticlesDraftCreate__generate_article_id',
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

        article_draft_create = ArticlesDraftCreate({}, {}, self.dynamodb)

        article_content_before = self.article_content_table.scan()['Items']

        with self.assertRaises(ClientError):
            article_draft_create._ArticlesDraftCreate__create_article_content(params, article_id)

        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    def test_generate_article_id(self):
        articles_draft_create = ArticlesDraftCreate({}, {}, self.dynamodb)

        target_sort_key1 = 1521120784000001
        target_sort_key2 = 1521120784000002

        hashid1 = articles_draft_create._ArticlesDraftCreate__generate_article_id(target_sort_key1)
        hashid2 = articles_draft_create._ArticlesDraftCreate__generate_article_id(target_sort_key2)

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
        prefix = 'http://'

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
