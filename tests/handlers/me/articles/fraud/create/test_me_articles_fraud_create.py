import os
import json
from tests_util import TestsUtil
from unittest import TestCase
from me_articles_fraud_create import MeArticlesFraudCreate
from unittest.mock import patch, MagicMock
from boto3.dynamodb.conditions import Key


class TestMeArticlesFraudCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create article_fraud_user_table
        cls.article_fraud_user_table_items = [
            {
                'article_id': 'testid000000',
                'user_id': 'test01',
                'created_at': 1520150272
            },
            {
                'article_id': 'testid000001',
                'user_id': 'test01',
                'created_at': 1520150273
            },
            {
                'article_id': 'testid000002',
                'user_id': 'test02',
                'created_at': 1520150274
            },
            {
                'article_id': 'testid000003',
                'user_id': 'test02',
                'created_at': 1520150275
            },
            {
                'article_id': 'testid000004',
                'user_id': 'test02',
                'created_at': 1520150276
            },
            {
                'article_id': 'testid000005',
                'user_id': 'test02',
                'created_at': 1520150277
            }
        ]
        TestsUtil.create_table(
            cls.dynamodb,
            os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'],
            cls.article_fraud_user_table_items
        )

        # create article_info_table
        article_info_table_items = [
            {
                'article_id': 'testid000000',
                'status': 'public',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'status': 'public',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'status': 'draft',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000003',
                'status': 'public',
                'sort_key': 1520150272000003
            },
            {
                'article_id': 'testid000004',
                'status': 'public',
                'sort_key': 1520150272000004
            },
            {
                'article_id': 'testid000005',
                'status': 'public',
                'sort_key': 1520150272000005
            },
        ]
        TestsUtil.create_table(
            cls.dynamodb,
            os.environ['ARTICLE_INFO_TABLE_NAME'],
            article_info_table_items
        )

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        test_function = MeArticlesFraudCreate(params, {}, self.dynamodb)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('time.time', MagicMock(return_value=1520150272000003))
    def test_main_ok_exist_article_id(self):
        params = {
            'pathParameters': {
                'article_id': self.article_fraud_user_table_items[0]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03'
                    }
                }
            }
        }

        article_fraud_user_table = self.dynamodb.Table(os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'])
        article_fraud_user_before = article_fraud_user_table.scan()['Items']

        article_fraud_user = MeArticlesFraudCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_fraud_user.main()

        article_fraud_user_after = article_fraud_user_table.scan()['Items']

        target_article_id = params['pathParameters']['article_id']
        target_user_id = params['requestContext']['authorizer']['claims']['cognito:username']

        article_fraud_user = self.get_article_fraud_user(target_article_id, target_user_id)

        expected_items = {
            'article_id': target_article_id,
            'user_id': target_user_id,
            'created_at': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_fraud_user_after), len(article_fraud_user_before) + 1)
        article_fraud_user_param_names = ['article_id', 'user_id', 'created_at']
        for key in article_fraud_user_param_names:
            self.assertEqual(expected_items[key], article_fraud_user[key])

    @patch('time.time', MagicMock(return_value=1520150272000003))
    def test_main_ok_added_reason(self):
        params = {
            'pathParameters': {
                'article_id': self.article_fraud_user_table_items[1]['article_id']
            },
            'body': json.dumps({
                'reason': 'violence'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03'
                    }
                }
            }
        }

        article_fraud_user_table = self.dynamodb.Table(os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'])
        article_fraud_user_before = article_fraud_user_table.scan()['Items']

        article_fraud_user = MeArticlesFraudCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_fraud_user.main()

        article_fraud_user_after = article_fraud_user_table.scan()['Items']

        target_article_id = params['pathParameters']['article_id']
        target_user_id = params['requestContext']['authorizer']['claims']['cognito:username']
        body = json.loads(params['body'])
        target_reason = body.get('reason')

        article_fraud_user = self.get_article_fraud_user(target_article_id, target_user_id)

        expected_items = {
            'article_id': target_article_id,
            'user_id': target_user_id,
            'reason': target_reason,
            'created_at': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_fraud_user_after), len(article_fraud_user_before) + 1)
        article_fraud_user_param_names = [
            'article_id',
            'user_id',
            'reason',
            'created_at'
        ]
        for key in article_fraud_user_param_names:
            self.assertEqual(expected_items[key], article_fraud_user[key])

    @patch('time.time', MagicMock(return_value=1520150272000003))
    def test_main_ok_reason_is_plagiarism(self):
        params = {
            'pathParameters': {
                'article_id': self.article_fraud_user_table_items[3]['article_id']
            },
            'body': json.dumps({
                'reason': 'plagiarism',
                'plagiarism_url': 'http://test.com',
                'plagiarism_description': 'plagiarism description',
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03'
                    }
                }
            }
        }

        article_fraud_user_table = self.dynamodb.Table(os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'])
        article_fraud_user_before = article_fraud_user_table.scan()['Items']

        article_fraud_user = MeArticlesFraudCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_fraud_user.main()

        article_fraud_user_after = article_fraud_user_table.scan()['Items']

        target_article_id = params['pathParameters']['article_id']
        target_user_id = params['requestContext']['authorizer']['claims']['cognito:username']
        body = json.loads(params['body'])
        target_reason = body.get('reason')
        target_plagiarism_url = body.get('plagiarism_url')
        target_plagiarism_description = body.get('plagiarism_description')

        article_fraud_user = self.get_article_fraud_user(target_article_id, target_user_id)

        expected_items = {
            'article_id': target_article_id,
            'user_id': target_user_id,
            'reason': target_reason,
            'plagiarism_url': target_plagiarism_url,
            'plagiarism_description': target_plagiarism_description,
            'created_at': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_fraud_user_after), len(article_fraud_user_before) + 1)
        article_fraud_user_param_names = [
            'article_id',
            'user_id',
            'reason',
            'plagiarism_url',
            'plagiarism_description',
            'created_at'
        ]
        for key in article_fraud_user_param_names:
            self.assertEqual(expected_items[key], article_fraud_user[key])

    @patch('time.time', MagicMock(return_value=1520150272000003))
    def test_main_ok_reason_is_other(self):
        params = {
            'pathParameters': {
                'article_id': self.article_fraud_user_table_items[4]['article_id']
            },
            'body': json.dumps({
                'reason': 'other',
                'illegal_content': 'illegal content'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03'
                    }
                }
            }
        }

        article_fraud_user_table = self.dynamodb.Table(os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'])
        article_fraud_user_before = article_fraud_user_table.scan()['Items']

        article_fraud_user = MeArticlesFraudCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_fraud_user.main()

        article_fraud_user_after = article_fraud_user_table.scan()['Items']

        target_article_id = params['pathParameters']['article_id']
        target_user_id = params['requestContext']['authorizer']['claims']['cognito:username']
        body = json.loads(params['body'])
        target_reason = body.get('reason')
        target_illegal_content = body.get('illegal_content')

        article_fraud_user = self.get_article_fraud_user(target_article_id, target_user_id)

        expected_items = {
            'article_id': target_article_id,
            'user_id': target_user_id,
            'reason': target_reason,
            'illegal_content': target_illegal_content,
            'created_at': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_fraud_user_after), len(article_fraud_user_before) + 1)
        article_fraud_user_param_names = [
            'article_id',
            'user_id',
            'reason',
            'illegal_content',
            'created_at'
        ]
        for key in article_fraud_user_param_names:
            self.assertEqual(expected_items[key], article_fraud_user[key])

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000002'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test04'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_fraud_create.DBUtil', mock_lib):
            MeArticlesFraudCreate(event=params, context={}, dynamodb=self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertTrue(args[0])
            self.assertTrue(args[1])
            self.assertEqual(kwargs['status'], 'public')

    def test_main_ng_exist_user_id(self):
        params = {
            'pathParameters': {
                'article_id': self.article_fraud_user_table_items[0]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_fraud_user_table_items[0]['user_id']
                    }
                }
            }
        }

        response = MeArticlesFraudCreate(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_params(self):
        params = {}

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

    def test_validation_invalid_reason(self):
        body = {
            'body': json.dumps({'reason': 'abcde'})
        }
        params = dict(self.get_parameters_other_than_body_for_validate(), **body)
        self.assert_bad_request(params)

    def test_validation_required_plagiarism_detail_when_reason_is_plagiarism(self):
        body = {
            'body': json.dumps(
                {
                    'reason': 'plagiarism'
                }
            )
        }
        params = dict(self.get_parameters_other_than_body_for_validate(), **body)
        self.assert_bad_request(params)

    def test_validation_invalid_plagiarism_url_when_reason_is_plagiarism(self):
        body = {
            'body': json.dumps(
                {
                    'reason': 'plagiarism',
                    'plagiarism_url': 'aaa'
                }
            )
        }
        params = dict(self.get_parameters_other_than_body_for_validate(), **body)
        self.assert_bad_request(params)

    def test_validation_required_illegal_content_when_reason_is_illegal(self):
        body = {
            'body': json.dumps(
                {
                    'reason': 'illegal'
                }
            )
        }
        params = dict(self.get_parameters_other_than_body_for_validate(), **body)
        self.assert_bad_request(params)

    def test_validation_required_illegal_content_when_reason_is_other(self):
        body = {
            'body': json.dumps(
                {
                    'reason': 'other'
                }
            )
        }
        params = dict(self.get_parameters_other_than_body_for_validate(), **body)
        self.assert_bad_request(params)

    def test_validation_plagiarism_description_max(self):
        body = {
            'body': json.dumps(
                {
                    'reason': 'plagiarism',
                    'plagiarism_description': u'あ' * 1001
                }
            )
        }
        params = dict(self.get_parameters_other_than_body_for_validate(), **body)
        self.assert_bad_request(params)

    def test_validation_illegal_content_max(self):
        body = {
            'body': json.dumps(
                {
                    'reason': 'illegal',
                    'illegal_content': u'あ' * 1001
                }
            )
        }
        params = dict(self.get_parameters_other_than_body_for_validate(), **body)
        self.assert_bad_request(params)

    def get_article_fraud_user(self, article_id, user_id):
        query_params = {
            'KeyConditionExpression': Key('article_id').eq(article_id) & Key('user_id').eq(user_id)
        }
        article_fraud_user_table = self.dynamodb.Table(os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'])
        return article_fraud_user_table.query(**query_params)['Items'][0]

    def get_parameters_other_than_body_for_validate(self):
        basic_params = {
            'pathParameters': {
                'article_id': self.article_fraud_user_table_items[5]['article_id']
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03'
                    }
                }
            }
        }
        return basic_params
