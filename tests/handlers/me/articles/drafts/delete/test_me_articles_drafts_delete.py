import os
import boto3
from elasticsearch import Elasticsearch
from unittest import TestCase
from me_articles_drafts_delete import MeArticlesDraftsDelete
from tests_util import TestsUtil


class TestMeArticlesDraftsDelete(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        os.environ['DOMAIN'] = 'example.com'

        cls.article_info_table = cls.dynamodb.Table('ArticleInfo')
        cls.article_content_table = cls.dynamodb.Table('ArticleContent')
        cls.article_content_edit_table = cls.dynamodb.Table('ArticleContentEdit')
        cls.article_history_table = cls.dynamodb.Table('ArticleHistory')
        cls.tag_table = cls.dynamodb.Table('Tag')

    def setUp(self):
        TestsUtil.delete_all_tables(self.dynamodb)

        article_info_items = [
            {
                'article_id': 'draftId00001',
                'user_id': 'test01',
                'status': 'draft',
                'tags': ['a', 'b', 'c'],
                'eye_catch_url': 'https://' + os.environ['DOMAIN'] + '/00001.png',
                'sort_key': 1520150272000000,
                'version': 2
            },
            {
                'article_id': 'draftId00002',
                'user_id': 'test01',
                'status': 'public',
                'sort_key': 1520150272000000,
                'version': 2
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], article_info_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        me_articles_drafts_publish_with_header = MeArticlesDraftsDelete(params, {}, dynamodb=self.dynamodb)
        response = me_articles_drafts_publish_with_header.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
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

        response = MeArticlesDraftsDelete(params, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

        article_info = self.article_info_table.get_item(Key={'article_id': params['pathParameters']['article_id']})['Item']
        self.assertEqual(article_info['status'], 'delete')

    def test_main_ng_with_public_article(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId00002'
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

        response = MeArticlesDraftsDelete(params, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_article_id(self):
        params = {
            'queryStringParameters': {},
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

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 13,
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

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 11,
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

        self.assert_bad_request(params)
