import copy
import json
import os

from jsonschema import ValidationError
from tests_util import TestsUtil
from unittest import TestCase
from me_articles_fraud_create import MeArticlesFraudCreate
from unittest.mock import patch, MagicMock
from boto3.dynamodb.conditions import Key


class TestMeArticlesFraudCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        # create article_fraud_user_table
        self.article_fraud_user_table_items = [
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
                'created_at': 1520150273
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'],
            self.article_fraud_user_table_items
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
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['ARTICLE_INFO_TABLE_NAME'],
            article_info_table_items
        )

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

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
            'body': {
                'reason': 'copyright_violation',
                'origin_url': 'http://example.com',
                'free_text': 'A' * 400
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

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
            'reason': 'copyright_violation',
            'origin_url': 'http://example.com',
            'free_text': 'A' * 400,
            'created_at': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(article_fraud_user_after), len(article_fraud_user_before) + 1)
        article_fraud_user_param_names = ['article_id', 'user_id', 'created_at']
        for key in article_fraud_user_param_names:
            self.assertEqual(expected_items[key], article_fraud_user[key])

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000002'
            },
            'body': {
                'reason': 'copyright_violation',
                'origin_url': 'http://example.com',
                'free_text': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test04',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

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
            'body': {
                'reason': 'copyright_violation',
                'origin_url': 'http://example.com',
                'free_text': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_fraud_user_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        response = MeArticlesFraudCreate(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'pathParameters': {
                'article_id': 'A' * 13
            },
            'body': {
                'reason': 'copyright_violation',
                'origin_url': 'http://example.com',
                'free_text': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
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
            'pathParameters': {
                'article_id': 'A' * 11
            },
            'body': {
                'reason': 'copyright_violation',
                'origin_url': 'http://example.com',
                'free_text': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_origin_url_max(self):
        base_url = 'http://example.com/'
        params = {
            'pathParameters': {
                'article_id': 'testid000000'
            },
            'body': {
                'reason': 'copyright_violation',
                'origin_url': base_url + 'A' * (2048 - len(base_url) + 1),
                'free_text': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_origin_required_with_copyright_violation(self):
        invalid_value = [None, '']

        for value in invalid_value:
            params = {
                'pathParameters': {
                    'article_id': 'testid000000'
                },
                'body': {
                    'reason': 'copyright_violation',
                    'origin_url': value,
                    'free_text': 'hogefugapiyo'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'test03',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }

            params['body'] = json.dumps(params['body'])

            self.assert_bad_request(params)

    def test_validation_origin_allow_none(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000000'
            },
            'body': {
                'reason': 'illegal_act',
                'origin_url': None,
                'free_text': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        response = MeArticlesFraudCreate(params, {}, self.dynamodb).main()
        self.assertEqual(response['statusCode'], 200)

    def test_validation_origin_url_format(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000000'
            },
            'body': {
                'reason': 'copyright_violation',
                'origin_url': 'hogehoge',
                'free_text': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_free_text_max(self):
        params = {
            'pathParameters': {
                'article_id': 'testid000000'
            },
            'body': {
                'reason': 'copyright_violation',
                'origin_url': 'http://example.com',
                'free_text': 'A' * 401
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test03',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        self.assert_bad_request(params)

    def test_validation_reason_enum(self):
        valid_target = [
            'illegal_act',
            'anything_contrary_to_public_order',
            'nuisance',
            'copyright_violation',
            'slander',
            'illegal_token_usage',
            'other'
        ]

        invalid_target = [
            None,
            '',
            'not_in_enum'
        ]

        def get_event(reason):
            return {
                'pathParameters': {
                    'article_id': 'testid000000'
                },
                'body': {
                    'reason': reason,
                    'origin_url': 'http://example.com',
                    'free_text': 'hogefugapiyo'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'test03',
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }

        for target in valid_target:
            me_article_fraud_create = MeArticlesFraudCreate({}, {}, self.dynamodb)
            event = get_event(target)
            me_article_fraud_create.event = event

            params = copy.deepcopy(event['body'])
            params.update(event['pathParameters'])
            me_article_fraud_create.params = params

            try:
                me_article_fraud_create.validate_params()
            except ValidationError:
                self.fail('No error is expected')

        for target in invalid_target:
            me_article_fraud_create = MeArticlesFraudCreate({}, {}, self.dynamodb)
            event = get_event(target)
            me_article_fraud_create.event = event

            params = copy.deepcopy(event['body'])
            params.update(event['pathParameters'])

            me_article_fraud_create.params = params

            with self.assertRaises(ValidationError):
                me_article_fraud_create.validate_params()

    def get_article_fraud_user(self, article_id, user_id):
        query_params = {
            'KeyConditionExpression': Key('article_id').eq(article_id) & Key('user_id').eq(user_id)
        }
        article_fraud_user_table = self.dynamodb.Table(os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'])
        return article_fraud_user_table.query(**query_params)['Items'][0]
