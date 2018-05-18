import os
from unittest import TestCase
from pre_signup import PreSignUp
from tests_util import TestsUtil


dynamodb = TestsUtil.get_dynamodb_client()


class TestPostConfirmation(TestCase):

    @classmethod
    def setUpClass(cls):
        items = [
            {'email': 'test@example.com', 'used': False},
            {'email': 'already@example.com', 'used': True},
        ]
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)
        TestsUtil.create_table(dynamodb, os.environ['BETA_USERS_TABLE_NAME'], items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(dynamodb)

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
        os.environ['BETA_MODE_FLAG'] = "0"
        event = {
                'userName': 'yamasita',
                'triggerSource': ''
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['userName'], 'yamasita')

    def test_correct_beta_user(self):
        os.environ['BETA_MODE_FLAG'] = "1"
        event = {
                'userName': 'yamasita',
                'request': {
                    'userAttributes': {
                        'phone_number': '',
                        'email': 'test@example.com'
                    }
                },
                'triggerSource': ''
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['userName'], 'yamasita')

    def test_already_used_email(self):
        os.environ['BETA_MODE_FLAG'] = "1"
        event = {
                'userName': 'yamasita2',
                'request': {
                    'userAttributes': {
                        'phone_number': '',
                        'email': 'already@example.com'
                    }
                }
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 500)

    def test_non_beta_user(self):
        os.environ['BETA_MODE_FLAG'] = "1"
        event = {
                'userName': 'yamasita2',
                'request': {
                    'userAttributes': {
                        'phone_number': '',
                        'email': 'hoge@example.com'
                    }
                }
        }
        presignup = PreSignUp(event=event, context="", dynamodb=dynamodb)
        response = presignup.main()
        self.assertEqual(response['statusCode'], 500)
