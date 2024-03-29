import json
import os
import boto3
import time

from elasticsearch import Elasticsearch
from tests_es_util import TestsEsUtil

import settings
from boto3.dynamodb.conditions import Key
from unittest import TestCase
from me_articles_drafts_publish import MeArticlesDraftsPublish
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil

from tag_util import TagUtil


class TestMeArticlesDraftsPublish(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()

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
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'draftId00002',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'draftId00003',
                'user_id': 'test01',
                'status': 'draft',
                'sort_key': 1520150272000000,
                'published_at': 1520150000
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
                'article_id': 'draftId00002',
                'title': 'sample_title2',
                'body': 'sample_body2'
            },
            {
                'article_id': 'draftId00003',
                'title': 'sample_title3',
                'body': 'sample_body3'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], article_content_items)

        article_content_edit_items = [
            {
                'article_id': 'draftId00002',
                'user_id': 'test01',
                'title': 'sample_title2_edit',
                'body': 'sample_body2_edit',
                'overview': 'sample_overview3_edit',
                'eye_catch_url': 'http://example.com/eye_catch_url3_edit'
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'], article_content_edit_items)

        article_history_items = [
            {
                'article_id': 'draftId00003',
                'title': 'sample_title3_history',
                'body': 'sample_body3_history',
                'created_at': int(time.time()) - 1
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_HISTORY_TABLE_NAME'], article_history_items)

        topic_items = [
            {'name': 'crypto', 'order': 1, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'fashion', 'order': 2, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'food', 'order': 3, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY}
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['TOPIC_TABLE_NAME'], topic_items)

        TestsUtil.create_table(self.dynamodb, os.environ['SCREENED_ARTICLE_TABLE_NAME'], [])

        TestsEsUtil.create_tag_index(self.elasticsearch)
        self.elasticsearch.indices.refresh(index="tags")

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)
        self.elasticsearch.indices.delete(index="tags", ignore=[404])

    def assert_bad_request(self, params):
        function = MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000000))
    @patch('time.time', MagicMock(return_value=1525000000.000000))
    def test_main_ok(self):
        TagUtil.create_tag(self.elasticsearch, 'a')
        TagUtil.create_tag(self.elasticsearch, 'B')

        self.elasticsearch.indices.refresh(index='tags')

        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'topic': 'crypto',
                'tags': ['A', 'B', 'C', 'D', 'E' * 25]
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_history_before = self.article_history_table.scan()['Items']
        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        response = MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_history_after = self.article_history_table.scan()['Items']
        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        self.assertEqual(response['statusCode'], 200)

        article_info = self.article_info_table.get_item(Key={'article_id': params['pathParameters']['article_id']})['Item']
        article_content = self.article_content_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']
        article_history = self.article_history_table.query(
            KeyConditionExpression=Key('article_id').eq(params['pathParameters']['article_id'])
        )['Items'][-1]

        self.assertEqual(article_info['status'], 'public')
        self.assertEqual(article_info['sort_key'], 1520150552000000)
        self.assertEqual(article_info['published_at'], 1525000000)
        self.assertEqual(article_info['sync_elasticsearch'], 1)
        self.assertEqual(article_info['topic'], 'crypto')
        self.assertEqual(article_info['tags'], ['a', 'B', 'C', 'D', 'E' * 25])
        self.assertEqual(article_content['title'], article_history['title'])
        self.assertEqual(article_content['body'], article_history['body'])
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_history_after) - len(article_history_before), 1)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), 0)

    def test_main_ok_with_article_content_edit(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00002'
            },
            'body': {
                'topic': 'crypto'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_history_before = self.article_history_table.scan()['Items']
        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        response = MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_history_after = self.article_history_table.scan()['Items']
        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        article_info = self.article_info_table.get_item(Key={'article_id': params['pathParameters']['article_id']})['Item']
        article_content = self.article_content_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']
        article_history = self.article_history_table.query(
            KeyConditionExpression=Key('article_id').eq(params['pathParameters']['article_id'])
        )['Items'][-1]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['status'], 'public')
        self.assertEqual(article_content['title'], article_history['title'])
        self.assertEqual(article_content['body'], article_history['body'])
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_history_after) - len(article_history_before), 1)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), -1)

    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000000))
    @patch('time.time', MagicMock(return_value=1999000000.000000))
    def test_main_ok_article_history_arleady_exists(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00003'
            },
            'body': {
                'topic': 'crypto'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        article_info_before = self.article_info_table.scan()['Items']
        article_history_before = self.article_history_table.scan()['Items']
        article_content_edit_before = self.article_content_edit_table.scan()['Items']

        response = MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()

        article_info_after = self.article_info_table.scan()['Items']
        article_history_after = self.article_history_table.scan()['Items']
        article_content_edit_after = self.article_content_edit_table.scan()['Items']

        article_info = self.article_info_table.get_item(Key={'article_id': params['pathParameters']['article_id']})['Item']
        article_content = self.article_content_table.get_item(
            Key={'article_id': params['pathParameters']['article_id']}
        )['Item']
        article_history = self.article_history_table.query(
            KeyConditionExpression=Key('article_id').eq(params['pathParameters']['article_id'])
        )['Items'][-1]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(article_info['status'], 'public')
        self.assertEqual(article_content['title'], article_history['title'])
        self.assertEqual(article_content['body'], article_history['body'])
        self.assertEqual(article_info['sort_key'], 1520150272000000)
        self.assertEqual(article_info['published_at'], 1520150000)
        self.assertEqual(len(article_info_after) - len(article_info_before), 0)
        self.assertEqual(len(article_history_after) - len(article_history_before), 1)
        self.assertEqual(len(article_content_edit_after) - len(article_content_edit_before), 0)

    @patch("me_articles_drafts_publish.TagUtil.create_and_count", MagicMock(side_effect=Exception()))
    def test_create_and_count_raise_exception(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'topic': 'crypto',
                'tags': ['A']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        response = MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()

        self.assertEqual(response['statusCode'], 200)

    def test_call_tag_util_methods(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'topic': 'crypto',
                'tags': ['A']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        mock_lib.get_tags_with_name_collation.return_value = ['A']
        with patch('me_articles_drafts_publish.TagUtil', mock_lib):
            MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()

            self.assertTrue(mock_lib.validate_tags.called)
            args, _ = mock_lib.validate_tags.call_args
            self.assertEqual(args[0], ['A'], 'test01')

            self.assertTrue(mock_lib.get_tags_with_name_collation.called)
            args, _ = mock_lib.get_tags_with_name_collation.call_args
            self.assertEqual(args[1], ['A'])

            self.assertTrue(mock_lib.create_and_count.called)
            args, _ = mock_lib.create_and_count.call_args

            self.assertTrue(args[0])
            self.assertEqual(args[1], ['a', 'b', 'c'])
            self.assertEqual(args[2], ['A'])

    def test_call_validate_array_unique(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'topic': 'crypto',
                'tags': ['A', 'B', 'C', 'D', 'E' * 25]
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()

        with patch('me_articles_drafts_publish.ParameterUtil', mock_lib):
            MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()

            self.assertTrue(mock_lib.validate_array_unique.called)
            args, kwargs = mock_lib.validate_array_unique.call_args
            self.assertEqual(args[0], ['A', 'B', 'C', 'D', 'E' * 25])
            self.assertEqual(args[1], 'tags')
            self.assertEqual(kwargs['case_insensitive'], True)

    def test_call_validate_methods(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {
                'topic': 'crypto'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_articles_drafts_publish.DBUtil', mock_lib):
            MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()

            self.assertTrue(mock_lib.validate_article_existence.called)
            args, kwargs = mock_lib.validate_article_existence.call_args
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertTrue(kwargs['user_id'])
            self.assertEqual(kwargs['status'], 'draft')

            self.assertTrue(mock_lib.validate_topic.called)
            args, kwargs = mock_lib.validate_topic.call_args
            self.assertTrue(args[0])
            self.assertEqual(args[1], 'crypto')

    def test_validation_not_exists_private_eth_address(self):
        params = {
            'queryStringParameters': {},
            'body': {
                'topic': 'crypto'
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
        response = MeArticlesDraftsPublish(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '{"message": "Invalid parameter: not exists private_eth_address"}')

    def test_validation_with_no_article_id(self):
        params = {
            'queryStringParameters': {},
            'body': {
                'topic': 'crypto'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 13,
            },
            'body': {
                'topic': 'crypto'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 11,
            },
            'body': {
                'topic': 'crypto'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_with_no_topic(self):
        params = {
            'pathParameters': {
                'article_id': 'draftId00001'
            },
            'body': {},
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }

        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_topic_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'draftId00001',
            },
            'body': {
                'topic': 'A' * 21
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_many_tags(self):
        params = {
            'queryStringParameters': {
                'article_id': 'draftId00001',
            },
            'body': {
                'topic': 'crypto',
                'tags': ['A', 'B', 'C', 'D', 'E', 'F']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_tag_name_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'draftId00001',
            },
            'body': {
                'topic': 'crypto',
                'tags': ['A', 'B', 'C', 'D', 'E' * 26]
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_tag_name_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'draftId00001',
            },
            'body': {
                'topic': 'crypto',
                'tags': ['A', 'B', 'C', 'D', '']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test01',
                        'custom:private_eth_address': '0x1234567890123456789012345678901234567890',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)
