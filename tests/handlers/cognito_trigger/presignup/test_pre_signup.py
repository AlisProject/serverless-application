import os
import boto3
from unittest import TestCase
from pre_signup import PreSignUp
from tests_util import TestsUtil


dynamodb = TestsUtil.get_dynamodb_client()


class TestPostConfirmation(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_validate_ng_too_short(self):
        event = {
                'version': '1',
                'region': 'us-east-1',
                'userPoolId': 'us-east-xxxxxxxx',
                'userName': 'y2',
                'callerContext': {
                    'awsSdkVersion': 'aws-sdk-js-2.6.4',
                    'clientId': 'xxxxx'
                },
                'triggerSource': 'PreSignUp_SignUp',
                'request': {
                    'userAttributes': {
                        'phone_number': '',
                        'email': 'y2@example.net'
                    },
                    'validationData': None
                },
                'response': {
                    'autoConfirmUser': False,
                    'autoVerifyEmail': False,
                    'autoVerifyPhone': False
                }
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 400)

    def test_validate_ng_too_long(self):
        event = {
                'userName': 'y2hogheogehgeoihgeoigewgheoighweoighwe'
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 400)

    def test_validate_ng_name(self):
        event = {
                'userName': 'admin'
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 400)

    def test_validate_ng_char(self):
        event = {
                'userName': 'yamasita!'
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 400)

    def test_validate_ng_head_hyphen(self):
        event = {
                'userName': '-yamasita'
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 400)

    def test_validate_ng_end_hyphen(self):
        event = {
                'userName': 'yamasita-'
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 400)

    def test_validate_ng_double_hyphen(self):
        event = {
                'userName': 'ya--masita'
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 400)

    def test_validate_ok(self):
        event = {
                'userName': 'yamasita'
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['userName'], 'yamasita')
