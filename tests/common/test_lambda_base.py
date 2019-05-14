import json

from tests_util import TestsUtil
from unittest import TestCase
from unittest.mock import MagicMock
from jsonschema import ValidationError
from lambda_base import LambdaBase
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError


class TestLambdaBase(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

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
