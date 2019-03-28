import os
import json
from unittest import TestCase
from me_articles_purchased_index import MeArticlesPurchasedIndex
from tests_util import TestsUtil


class TestMeArticlesPurchasedIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        paid_articles_items = [
            {
                'article_id': 'publicId0000',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150271000000,
                'history_created_at': 1520150271,
                'created_at': 1520150271,
                'transaction': '0x0000000000000000000000000000000000000009',
                'status': 'done',
                'price': 1
            },
            {
                'article_id': 'publicId0001',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000000,
                'history_created_at': 1520150272,
                'created_at': 1520150272,
                'transaction': '0x0000000000000000000000000000000000000000',
                'status': 'done',
                'price': 100
            },
            {
                'article_id': 'publicId0002',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000001,
                'history_created_at': 1520150273,
                'created_at': 1520150273,
                'transaction': '0x0000000000000000000000000000000000000001',
                'status': 'doing',
                'price': 200
            },
            {
                'article_id': 'draftId00001',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000002,
                'history_created_at': 1520150274,
                'created_at': 1520150274,
                'transaction': '0x0000000000000000000000000000000000000002',
                'status': 'done',
                'price': 300
            },
            {
                'article_id': 'publicId0003',
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150272000003,
                'history_created_at': 1520150275,
                'created_at': 1520150275,
                'transaction': '0x0000000000000000000000000000000000000003',
                'status': 'done',
                'price': 400
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], paid_articles_items)

        cls.article_info_items = [
            {
                'article_id': 'publicId0001',
                'user_id': 'test_article_user_01',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'publicId0002',
                'user_id': 'test_article_user_01',
                'status': 'public',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'draftId00001',
                'user_id': 'test_article_user_01',
                'status': 'draft',
                'sort_key': 1520150272000002,
                'price': 300
            },
            {
                'article_id': 'publicId0003',
                'user_id': 'test_article_user_01',
                'status': 'public',
                'sort_key': 1520150272000003,
                'price': 400
            }
        ]

        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], cls.article_info_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesPurchasedIndex(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'limit': '2'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        expected_items = [
            self.article_info_items[3],
            self.article_info_items[2]
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_evaluated_key(self):
        params = {
            'queryStringParameters': {
                'limit': '1',
                'article_id': 'draftId00001',
                'sort_key': '1520150272000002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        expected_items = [
            self.article_info_items[0]
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ng_with_no_article_info(self):
        params = {
            'queryStringParameters': {
                'limit': '1',
                'article_id': 'publicId0001',
                'sort_key': '1520150272000000'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 500)

    def test_main_ok_with_only_sort_key(self):
        params = {
            'queryStringParameters': {
                'sort_key': '1520150272000002',
                'limit': '1'
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

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        not_expected_response = [
            self.article_info_items[0]
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertNotEqual(json.loads(response['body'])['Items'], not_expected_response)

    def test_main_ok_with_evaluated_key_with_no_limit(self):
        paid_articles_table = self.dynamodb.Table('PaidArticles')

        for i in range(11):
            paid_articles_table.put_item(Item={
                'article_id': 'test_limit_number' + str(i),
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_01',
                'sort_key': 1520150273000000 + i,
                'history_created_at': 152015028 + i,
                'created_at': 152015028 + i,
                'transaction': '0x100000000000000000000000000000000000000' + str(i),
                'status':  'done',
                'price': 1000
            })

        article_info_table = self.dynamodb.Table('ArticleInfo')

        for i in range(11):
            article_info_table.put_item(Item={
                'user_id': 'test_user_id',
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i
            })

        params = {
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_main_ok_with_doing_articles(self):
        paid_articles_table = self.dynamodb.Table('PaidArticles')

        for i in range(10):
            # done, doing, doing, done, doing, doing, done, done, done, done
            # の順でステータスが検索されるようにテストデータを生成する
            status = 'done' if i % 3 == 0 or i < 4 else 'doing'

            paid_articles_table.put_item(Item={
                'article_id': 'test_limit_' + str(i),
                'article_user_id': 'test_article_user_01',
                'user_id': 'test_user_id',
                'sort_key': 1520150273000000 + i,
                'history_created_at': 152015028 + i,
                'created_at': 152015028 + i,
                'transaction': '0x100000000000000000000000000000000000000' + str(i),
                'status': status,
                'price': 1000
                }
            )

        article_info_table = self.dynamodb.Table('ArticleInfo')

        for i in range(10):
            article_info_table.put_item(Item={
                'user_id': 'test_user_id',
                'article_id': 'test_limit_' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i
            })

        params = {
            'queryStringParameters': {
                'limit': '3'
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

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 3)

        expected_evaluated_key = {
            'article_id': 'test_limit_3',
            'user_id': 'test_user_id',
            'sort_key': 1520150273000003
        }
        self.assertEqual(json.loads(response['body'])['LastEvaluatedKey'], expected_evaluated_key)

    def test_main_with_no_recourse(self):
        params = {
            'queryStringParameters': {
                'limit': '3'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'not_exists_user_id',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], [])

    def test_validation_with_no_query_params(self):
        params = {
            'queryStringParameters': None,
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

        response = MeArticlesPurchasedIndex(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

    def test_validation_limit_type(self):
        params = {
            'queryStringParameters': {
                'limit': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_max(self):
        params = {
            'queryStringParameters': {
                'limit': '101'
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_min(self):
        params = {
            'queryStringParameters': {
                'limit': '0'
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 13
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'queryStringParameters': {
                'article_id': 'A' * 11
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_type(self):
        params = {
            'queryStringParameters': {
                'sort_key': 'ALIS'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_max(self):
        params = {
            'queryStringParameters': {
                'sort_key': '2147483647000001'
            }
        }

        self.assert_bad_request(params)

    def test_validation_sort_key_min(self):
        params = {
            'queryStringParameters': {
                'article_id': '0'
            }
        }

        self.assert_bad_request(params)
