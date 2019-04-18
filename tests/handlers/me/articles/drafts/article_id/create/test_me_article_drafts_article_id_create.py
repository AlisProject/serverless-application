from unittest import TestCase
from me_articles_drafts_article_id_create import MeArticlesDraftsArticleIdCreate
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from tests_util import TestsUtil
import os
import json


class TestMeArticlesDraftsArticleIdCreate(TestCase):
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
        function = MeArticlesDraftsArticleIdCreate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch(
        "me_articles_drafts_article_id_create.MeArticlesDraftsArticleIdCreate._"
        "MeArticlesDraftsArticleIdCreate__generate_article_id",
        MagicMock(return_value='HOGEHOGEHOGE'))
    def test_main_ok(self):
        params = {
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

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        me_articles_drafts_article_id_create = MeArticlesDraftsArticleIdCreate(params, {}, self.dynamodb)

        response = me_articles_drafts_article_id_create.main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(json.loads(response['body']), {'article_id': 'HOGEHOGEHOGE'})

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(params['requestContext']['authorizer']['claims']['cognito:username'],
                         article_info_after[0]['user_id'])
        self.assertEqual(len(article_info_after) - len(article_info_before), 1)
        self.assertEqual(len(article_content_after) - len(article_content_before), 1)

    @patch(
        "me_articles_drafts_article_id_create.MeArticlesDraftsArticleIdCreate._"
        "MeArticlesDraftsArticleIdCreate__create_article_info",
        MagicMock(side_effect=Exception()))
    def test_main_with_internal_server_error_on_create_article_info(self):
        params = {
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

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = MeArticlesDraftsArticleIdCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body'])['message'], 'Internal server error')
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch(
        'me_articles_drafts_article_id_create.MeArticlesDraftsArticleIdCreate.'
        '_MeArticlesDraftsArticleIdCreate__generate_article_id',
        MagicMock(return_value='HOGEHOGEHOGE'))
    @patch(
        'me_articles_drafts_article_id_create.MeArticlesDraftsArticleIdCreate.'
        '_MeArticlesDraftsArticleIdCreate__create_article_content',
        MagicMock(side_effect=Exception()))
    def test_main_with_error_on_create_article_content(self):
        params = {
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

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = MeArticlesDraftsArticleIdCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'article_id': 'HOGEHOGEHOGE'})
        self.assertEqual(len(article_info_after) - len(article_info_before), 1)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch(
        'me_articles_drafts_article_id_create.MeArticlesDraftsArticleIdCreate.'
        '_MeArticlesDraftsArticleIdCreate__generate_article_id',
        MagicMock(return_value='HOGEHOGEHOGE'))
    def test_main_with_article_id_already_exists(self):
        self.article_info_table.put_item(
            Item={
                'article_id': 'HOGEHOGEHOGE',
                'user_id': 'USER_ID',
                'status': 'draft',
                'sort_key': 1521120784000001,
            }
        )

        params = {
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

        article_info_before = self.article_info_table.scan()['Items']
        article_content_before = self.article_content_table.scan()['Items']

        response = MeArticlesDraftsArticleIdCreate(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), {'message': 'Already exists'})
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    @patch(
        'me_articles_drafts_article_id_create.MeArticlesDraftsArticleIdCreate.'
        '_MeArticlesDraftsArticleIdCreate__generate_article_id',
        MagicMock(return_value='HOGEHOGEHOGE'))
    def test_create_article_content_with_article_id_already_exists(self):
        self.article_content_table.put_item(
            Item={
                'article_id': 'HOGEHOGEHOGE',
                'title': 'test_title',
                'body': 'test_body'
            }
        )

        article_id = 'HOGEHOGEHOGE'

        article_draft_article_id_create = MeArticlesDraftsArticleIdCreate({}, {}, self.dynamodb)

        article_content_before = self.article_content_table.scan()['Items']

        with self.assertRaises(ClientError):
            article_draft_article_id_create._MeArticlesDraftsArticleIdCreate__create_article_content(article_id)

        article_content_after = self.article_content_table.scan()['Items']

        self.assertEqual(len(article_content_after) - len(article_content_before), 0)

    def test_generate_article_id(self):
        me_articles_drafts_article_id_create = MeArticlesDraftsArticleIdCreate({}, {}, self.dynamodb)

        target_sort_key1 = 1521120784000001
        target_sort_key2 = 1521120784000002

        hashid1 = me_articles_drafts_article_id_create._MeArticlesDraftsArticleIdCreate__generate_article_id(
            target_sort_key1)
        hashid2 = me_articles_drafts_article_id_create._MeArticlesDraftsArticleIdCreate__generate_article_id(
            target_sort_key2)

        self.assertNotEqual(hashid1, hashid2)
        self.assertEqual(len(hashid1), 12)
        self.assertEqual(len(hashid2), 12)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)
