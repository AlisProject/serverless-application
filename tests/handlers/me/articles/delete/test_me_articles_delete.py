from unittest import TestCase
from me_articles_delete import MeArticlesDelete
from tests_util import TestsUtil
import os


class TestMeArticlesDelete(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        self.article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        self.article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        self.deleted_draft_article_info_table = self.dynamodb.Table(os.environ['DELETED_DRAFT_ARTICLE_INFO_TABLE_NAME'])
        self.deleted_draft_article_content_table = self.dynamodb.Table(os.environ['DELETED_DRAFT_ARTICLE_CONTENT_TABLE_NAME'])
        self.article_info_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'article_user01',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'draftId00002',
                'user_id': 'article_user02',
                'status': 'draft',
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], self.article_info_items)

        self.article_content_items = [
            {
                'article_id': 'publicId0001',
                'body': 'body',
                'created_at': 1520150272,
                'title': 'test-title01'
            },
            {
                'article_id': 'draftId00002',
                'body': 'body',
                'created_at': 1520150272,
                'title': 'test-title02'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], self.article_content_items)

        self.history_article_items = [
            {
                'article_id': 'publicId0001',
                'created_at': 1520150272,
                'body': 'hoge',
                'title': 'test-title01'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_HISTORY_TABLE_NAME'], self.history_article_items)
        TestsUtil.create_table(self.dynamodb, os.environ['DELETED_DRAFT_ARTICLE_INFO_TABLE_NAME'], [])
        TestsUtil.create_table(self.dynamodb, os.environ['DELETED_DRAFT_ARTICLE_CONTENT_TABLE_NAME'], [])

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_items[1]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'article_user02',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        article_info_before = self.article_info_table.scan()['Items']
        deleted_draft_article_info_before = self.deleted_draft_article_info_table.scan()['Items']

        article_content_before = self.article_content_table.scan()['Items']
        deleted_draft_article_content_before = self.deleted_draft_article_content_table.scan()['Items']

        response = MeArticlesDelete(params, {}, self.dynamodb).main()

        article_info_after = self.article_info_table.scan()['Items']
        deleted_draft_article_info_after = self.deleted_draft_article_info_table.scan()['Items']

        article_content_after = self.article_content_table.scan()['Items']
        deleted_draft_article_content_after = self.deleted_draft_article_content_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_info_after) - len(article_info_before), -1)
        self.assertEqual(len(deleted_draft_article_info_after) - len(deleted_draft_article_info_before), 1)
        self.assertEqual(len(article_content_after) - len(article_content_before), -1)
        self.assertEqual(len(deleted_draft_article_content_after) - len(deleted_draft_article_content_before), 1)

    def test_main_already_public_article(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_items[0]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'article_user01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesDelete(params, {}, self.dynamodb).main()
        self.assertEqual(response['statusCode'], 404)

    def test_not_authorize_error(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_items[1]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'hoge',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesDelete(params, {}, self.dynamodb).main()
        self.assertEqual(response['statusCode'], 403)
