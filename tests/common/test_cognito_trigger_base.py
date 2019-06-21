from tests_util import TestsUtil
from unittest import TestCase
from unittest.mock import MagicMock
from jsonschema import ValidationError
from cognito_trigger_base import CognitoTriggerBase


class TestCognitoTriggerBase(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    class TestLambdaImpl(CognitoTriggerBase):
        def get_schema(self):
            pass

        def validate_params(self):
            pass

        def exec_main_proc(self):
            pass

    def test_catch_validation_error(self):
        lambda_impl = self.TestLambdaImpl({}, {}, self.dynamodb)
        lambda_impl.exec_main_proc = MagicMock(side_effect=ValidationError('not valid'))
        with self.assertRaises(Exception) as e:
            lambda_impl.main()
        self.assertEqual('not valid', str(e.exception))

    def test_catch_exception_error(self):
        lambda_impl = self.TestLambdaImpl({}, {}, self.dynamodb)
        lambda_impl.exec_main_proc = MagicMock(side_effect=Exception('exception'))
        with self.assertRaises(Exception) as e:
            lambda_impl.main()
        self.assertEqual('Internal server error', str(e.exception))
