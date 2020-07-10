import os
import json
from tests_util import TestsUtil
from unittest import TestCase
from unittest.mock import patch, MagicMock
from jsonschema import ValidationError
from lambda_base import LambdaBase
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError


class TestLambdaBase(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        cls.dynamodb = TestsUtil.get_dynamodb_client()
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)
        cls.user_configurations_items = [
            {
                'user_id': 'test-user1',
                'private_eth_address': '0x1234567890123456789012345678901234567890'
            },
            {
                'user_id': 'test-user2'
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'],
                               cls.user_configurations_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    class TestLambdaImpl(LambdaBase):
        def get_schema(self):
            pass

        def validate_params(self):
            pass

        def exec_main_proc(self):
            pass

    def test_catch_validation_error(self):
        lambda_impl = self.TestLambdaImpl({}, {}, self.dynamodb)
        lambda_impl.exec_main_proc = MagicMock(side_effect=ValidationError('not valid'))
        response = lambda_impl.main()
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body'])['message'], 'Invalid parameter: not valid')

    def test_catch_record_not_found_error(self):
        lambda_impl = self.TestLambdaImpl({}, {}, self.dynamodb)
        lambda_impl.exec_main_proc = MagicMock(side_effect=RecordNotFoundError('not found'))
        response = lambda_impl.main()
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body'])['message'], 'not found')

    def test_catch_not_authorized_error(self):
        lambda_impl = self.TestLambdaImpl({}, {}, self.dynamodb)
        lambda_impl.exec_main_proc = MagicMock(side_effect=NotAuthorizedError('not authorized'))
        response = lambda_impl.main()
        self.assertEqual(response['statusCode'], 403)
        self.assertEqual(json.loads(response['body'])['message'], 'not authorized')

    def test_catch_internal_server_error(self):
        lambda_impl = self.TestLambdaImpl({}, {}, self.dynamodb)
        lambda_impl.exec_main_proc = MagicMock(side_effect=Exception())
        response = lambda_impl.main()
        self.assertEqual(response['statusCode'], 500)

    def test_get_params_ok_not_exists_any_params(self):
        event = {}
        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        expected_params = {}
        self.assertEqual(expected_params, lambda_impl.params)

    def test_get_params_ok_exists_all_params(self):
        event = {
            'queryStringParameters': {
                'test_key1': 'test1'
            },
            'pathParameters': {
                'test_key2': 'test2',
                'test_key3': 'test3'

            },
            'body': json.dumps({'test_key4': 'test4'})
        }
        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        expected_params = {
            'test_key1': 'test1',
            'test_key2': 'test2',
            'test_key3': 'test3',
            'test_key4': 'test4'
        }
        self.assertEqual(expected_params, lambda_impl.params)

    def test_get_params_validation_json_error(self):
        event = {
            'queryStringParameters': {
                'test_key1': 'test1'
            },
            'pathParameters': {
                'test_key2': 'test2',
                'test_key3': 'test3'

            },
            'body': 'not json string'
        }
        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        response = lambda_impl.main()
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body'])['message'], 'Invalid parameter: body needs to be json string')

    def test_get_headers_ok_not_exists_any_params(self):
        event = {}
        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        expected_headers = {}
        self.assertEqual(expected_headers, lambda_impl.headers)

    def test_get_headers_ok(self):
        event = {
            'headers': {
                'test_key1': 'test1',
                'test_key2': 'test2'
            }
        }
        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        expected_headers = {
            'test_key1': 'test1',
            'test_key2': 'test2'
        }
        self.assertEqual(expected_headers, lambda_impl.headers)

    def test_update_event_ok(self):
        event = {
            'body': {
                'hoge': 'fuga'
            },
            'requestContext': {
                'authorizer': {
                    'principalId': 'oauth_user_id'
                }
            }
        }

        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        self.assertEqual('oauth_user_id',
                         lambda_impl.event['requestContext']['authorizer']['claims']['cognito:username'])
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['phone_number_verified'])
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['email_verified'])

    def test_update_event_ok_with_dynamodb(self):
        event = {
            'body': {
                'hoge': 'fuga'
            },
            'requestContext': {
                'authorizer': {
                    'principalId': 'oauth_user_id'
                }
            }
        }

        lambda_impl = self.TestLambdaImpl(event, {}, self.dynamodb)
        lambda_impl.main()
        self.assertEqual('oauth_user_id',
                         lambda_impl.event['requestContext']['authorizer']['claims']['cognito:username'])
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['phone_number_verified'])
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['email_verified'])

    def test_update_event_ok_exists_private_eth_address(self):
        event = {
            'body': {
                'hoge': 'fuga'
            },
            'requestContext': {
                'authorizer': {
                    'principalId': self.user_configurations_items[0]['user_id']
                }
            }
        }

        lambda_impl = self.TestLambdaImpl(event, {}, self.dynamodb)
        lambda_impl.main()
        self.assertEqual(self.user_configurations_items[0]['user_id'],
                         lambda_impl.event['requestContext']['authorizer']['claims']['cognito:username'])
        self.assertEqual(self.user_configurations_items[0]['private_eth_address'],
                         lambda_impl.event['requestContext']['authorizer']['claims']['custom:private_eth_address'])
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['phone_number_verified'])
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['email_verified'])

    def test_update_event_ok_not_exists_private_eth_address(self):
        event = {
            'body': {
                'hoge': 'fuga'
            },
            'requestContext': {
                'authorizer': {
                    'principalId': self.user_configurations_items[1]['user_id']
                }
            }
        }

        lambda_impl = self.TestLambdaImpl(event, {}, self.dynamodb)
        lambda_impl.main()
        self.assertEqual(self.user_configurations_items[1]['user_id'],
                         lambda_impl.event['requestContext']['authorizer']['claims']['cognito:username'])
        self.assertIsNone(lambda_impl.event['requestContext']['authorizer']['claims'].get('private_eth_address'))
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['phone_number_verified'])
        self.assertEqual('true', lambda_impl.event['requestContext']['authorizer']['claims']['email_verified'])

    def test_update_event_ok_not_updated(self):
        event = {
            'body': {
                'hoge': 'fuga'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id'
                    }
                }
            }
        }

        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        self.assertEqual('test_user_id',
                         lambda_impl.event['requestContext']['authorizer']['claims']['cognito:username'])

    def test_update_event_ok_with_no_authorizer(self):
        event = {
            'body': {
                'hoge': 'fuga'
            }
        }

        lambda_impl = self.TestLambdaImpl(event, {})
        lambda_impl.main()
        self.assertFalse(lambda_impl.event.get('requestContext'))

    def test_filter_event_for_log_ok(self):
        with patch('settings.not_logging_parameters', {"not_logging_param_1", "not_logging_param_2"}), \
                patch('logging.Logger.info') as mock_logger_info:

            event = {
                'body': '{"logging_param": "aaaaa", "not_logging_param_1": "bbbbb", "not_logging_param_2": "ccccc"}',
                'other_part': {}
            }
            lambda_impl = self.TestLambdaImpl(event, {})
            lambda_impl.exec_main_proc = MagicMock(side_effect=Exception())

            lambda_impl.main()

            mock_logger_info.assert_called_with({
                'body': '{"logging_param": "aaaaa", "not_logging_param_1": "xxxxx", "not_logging_param_2": "xxxxx"}',
                'other_part': {}
            })

    def test_filter_event_for_log_ok_with_no_body(self):
        with patch('logging.Logger.info') as mock_logger_info:

            event = {
                'other_part': {}
            }
            lambda_impl = self.TestLambdaImpl(event, {})
            lambda_impl.exec_main_proc = MagicMock(side_effect=Exception())

            lambda_impl.main()

            mock_logger_info.assert_called_with({
                'other_part': {}
            })

    def test_filter_event_for_log_ok_with_invalid_body(self):
        with patch('logging.Logger.info') as mock_logger_info:

            event = {
                'body': 'invalid body'
            }
            lambda_impl = self.TestLambdaImpl(event, {})
            lambda_impl.exec_main_proc = MagicMock(side_effect=Exception())

            lambda_impl.main()

            mock_logger_info.assert_called_with({
                'body': 'invalid body'
            })
