import os
import json
from unittest import TestCase
from me_articles_comments_index import MeArticlesCommentsIndex
from tests_util import TestsUtil

class TestMeArticlesCommentsIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        cls.comment_items = [
            {
                'comment_id': 'comment00001',
                'article_id': 'publicId0001',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000000,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00002',
                'article_id': 'publicId0001',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000001,
                'created_at': 1520150272,
                'text': 'コメントの内容2'
            },
            {
                'comment_id': 'comment00003',
                'article_id': 'publicId0001',
                'user_id': 'test_user_02',
                'sort_key': 1520150272000002,
                'created_at': 1520150272,
                'text': 'コメントの内容1'
            },
            {
                'comment_id': 'comment00004',
                'article_id': 'publicId0002',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000004,
                'created_at': 1520150272,
                'text': 'コメントの内容4'
            },
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_TABLE_NAME'], cls.comment_items)

    @classmethod
    def tearDownClass(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        response = MeArticlesCommentsIndex(params, {}, self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '2'
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        response = MeArticlesCommentsIndex (params, {}, self.dynamodb).main()

        expected_items = [self.comment_items[2], self.comment_items[1]]
        expected_last_evaluated_key = {
            'comment_id': self.comment_items[1]['comment_id'],
            'sort_key': self.comment_items[1]['sort_key'],
            'article_id': self.comment_items[1]['article_id']
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)
        self.assertEqual(json.loads(response['body'])['LastEvaluatedKey'], expected_last_evaluated_key)

    def test_main_with_evaluated_key(self):
        params = {
            'queryStringParameters': {
                'limit': '2',
                'comment_id': self.comment_items[1]['comment_id'],
                'sort_key': str(self.comment_items[1]['sort_key'])

            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        response = MeArticlesCommentsIndex(params, {}, self.dynamodb).main()

        expected_items = [self.comment_items[0]]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)
        self.assertIsNone(json.loads(response['body']).get('LastEvaluatedKey'))

    def test_main_with_no_limit(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        for i in range(11):
            comment_table.put_item(Item={
                    'comment_id': 'comment1000' + str(i),
                    'article_id': 'publicId0001',
                    'user_id': 'test_user_01',
                    'sort_key': 152015027200000 + i,
                    'created_at': 1520150272,
                    'text': 'コメントの内容'
                }
            )

        response = MeArticlesCommentsIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_validation_comment_id_max(self):
        params = {
            'queryStringParameters': {
                'comment_id': 'A' * 13
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

    def test_validation_limit_type(self):
        params = {
            'queryStringParameters': {
                'limit': 'ALIS'
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_max(self):
        params = {
            'queryStringParameters': {
                'limit': '101'
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_min(self):
        params = {
            'queryStringParameters': {
                'limit': '0'
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_type(self):
        params = {
            'queryStringParameters': {
                'sort_key': 'ALIS'
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_max(self):
        params = {
            'queryStringParameters': {
                'sort_key': '2147483647000001'
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_min(self):
        params = {
            'queryStringParameters': {
                'sort_key': '0'
            },
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        self.assert_bad_request(params)
