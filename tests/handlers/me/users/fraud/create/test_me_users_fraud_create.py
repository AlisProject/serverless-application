@patchimport copy
import json
import os

from jsonschema import ValidationError
from tests_util import TestsUtil
from unittest import TestCase
from me_users_fraud_create import MeUsersFraudCreate
from unittest.mock import patch, MagicMock


class TestMeUsersFraudCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.user_fraud_table_items = [
            {
                'target_user_id': 'testuser02',
                'user_id': 'testuser03',
                'created_at': 1520150272
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['USER_FRAUD_TABLE_NAME'],
            self.user_fraud_table_items
        )

        # create article_info_table
        self.user_items = [
            {
                'user_id': 'testuser01'
            },
            {
                'user_id': 'testuser02'
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['USERS_TABLE_NAME'],
            self.user_items
        )

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        test_function = MeUsersFraudCreate(params, {}, self.dynamodb)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('time.time', MagicMock(return_value=1520150272000003))
    def test_main_ok(self):
        params = {
            'pathParameters': {
                'user_id': self.user_items[0]['user_id']
            },
            'body': {
                'reason': 'illegal_act',
                'origin_url': 'http://example.com',
                'free_text': 'A' * 400
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'testuser02',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        user_fraud_table = self.dynamodb.Table(os.environ['USER_FRAUD_TABLE_NAME'])
        fraud_user_before = user_fraud_table.scan()['Items']

        article_fraud_user = MeUsersFraudCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_fraud_user.main()

        fraud_user_after = user_fraud_table.scan()['Items']

        target_user_id = params['pathParameters']['user_id']
        user_id = params['requestContext']['authorizer']['claims']['cognito:username']

        article_fraud_user = user_fraud_table.get_item(Key={'target_user_id': target_user_id, 'user_id': user_id})['Item']

        expected_items = {
            'target_user_id': target_user_id,
            'user_id': user_id,
            'reason': 'illegal_act',
            'free_text': 'A' * 400,
            'created_at': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(fraud_user_after), len(fraud_user_before) + 1)

        for key in expected_items.keys():
            self.assertEqual(expected_items[key], article_fraud_user[key])

    @patch('time.time', MagicMock(return_value=1520150272000003))
    def test_main_ok_empty_free_text(self):
        params = {
            'pathParameters': {
                'user_id': self.user_items[0]['user_id']
            },
            'body': {
                'reason': 'illegal_act',
                'origin_url': 'http://example.com',
                'free_text': ''
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'testuser02',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        user_fraud_table = self.dynamodb.Table(os.environ['USER_FRAUD_TABLE_NAME'])
        fraud_user_before = user_fraud_table.scan()['Items']

        article_fraud_user = MeUsersFraudCreate(event=params, context={}, dynamodb=self.dynamodb)
        response = article_fraud_user.main()

        fraud_user_after = user_fraud_table.scan()['Items']

        target_user_id = params['pathParameters']['user_id']
        user_id = params['requestContext']['authorizer']['claims']['cognito:username']

        article_fraud_user = user_fraud_table.get_item(Key={'target_user_id': target_user_id, 'user_id': user_id})['Item']

        expected_items = {
            'target_user_id': target_user_id,
            'user_id': user_id,
            'reason': 'illegal_act',
            'free_text': None,
            'created_at': 1520150272000003
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(fraud_user_after), len(fraud_user_before) + 1)

        for key in expected_items.keys():
            self.assertEqual(expected_items[key], article_fraud_user[key])

    def test_call_validate_user_existence(self):
        params = {
            'pathParameters': {
                'user_id': self.user_items[0]['user_id']
            },
            'body': {
                'reason': 'illegal_act',
                'origin_url': 'http://example.com',
                'free_text': ''
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'testuser02',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        mock_lib = MagicMock()
        with patch('me_users_fraud_create.DBUtil', mock_lib):
            MeUsersFraudCreate(event=params, context={}, dynamodb=self.dynamodb).main()
            args, _ = mock_lib.validate_user_existence.call_args

            self.assertTrue(mock_lib.validate_user_existence.called)
            self.assertEqual(args[0], self.dynamodb)
            self.assertEqual(args[1], params['pathParameters']['user_id'])

    def test_main_ng_report_myself(self):
        params = {
            'pathParameters': {
                'user_id': self.user_fraud_table_items[0]['target_user_id']
            },
            'body': {
                'reason': 'illegal_act',
                'origin_url': 'http://example.com',
                'free_text': 'A' * 400
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.user_fraud_table_items[0]['target_user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        response = MeUsersFraudCreate(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ng_exist_user_id(self):
        params = {
            'pathParameters': {
                'user_id': self.user_fraud_table_items[0]['target_user_id']
            },
            'body': {
                'reason': 'illegal_act',
                'origin_url': 'http://example.com',
                'free_text': 'A' * 400
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.user_fraud_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        response = MeUsersFraudCreate(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 400)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_origin_url_max(self):
        base_url = 'http://example.com/'
        params = {
            'pathParameters': {
                'user_id': self.user_fraud_table_items[0]['target_user_id']
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
                    'user_id': self.user_fraud_table_items[0]['target_user_id']
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
                'user_id': self.user_fraud_table_items[0]['target_user_id']
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
        response = MeUsersFraudCreate(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

    def test_validation_free_text_max(self):
        params = {
            'pathParameters': {
                'user_id': self.user_items[0]['user_id']
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
                    'user_id': self.user_items[0]['user_id']
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
            me_article_fraud_create = MeUsersFraudCreate({}, {}, self.dynamodb)
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
            me_article_fraud_create = MeUsersFraudCreate({}, {}, self.dynamodb)
            event = get_event(target)
            me_article_fraud_create.event = event

            params = copy.deepcopy(event['body'])
            params.update(event['pathParameters'])

            me_article_fraud_create.params = params

            with self.assertRaises(ValidationError):
                me_article_fraud_create.validate_params()

    def get_user_fraud(self, target_user_id, user_id):
        user_fraud_table = self.dynamodb.Table(os.environ['USER_FRAUD_TABLE_NAME'])

        return user_fraud_table.get_item(Key={'target_user_id': target_user_id, 'user_id': user_id})['Item']
