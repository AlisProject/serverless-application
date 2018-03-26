import boto3
import json
from unittest import TestCase
from unittest.mock import MagicMock
from jsonschema import ValidationError
from lambda_base import LambdaBase
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError


class TestLambdaBase(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

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
