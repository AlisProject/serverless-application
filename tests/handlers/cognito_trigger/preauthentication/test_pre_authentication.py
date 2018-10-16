import os
from unittest import TestCase
from pre_authentication import PreAuthentication
from tests_util import TestsUtil


dynamodb = TestsUtil.get_dynamodb_client()


class TestPreAuthentication(TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['EXTERNAL_PROVIDER_LOGIN_MARK'] = 'test_marker'
        external_provider_user_items = [
            {'external_provider_user_id': 'external_provider_user', 'password': 'password', 'user_id': 'user_name'}
        ]
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)
        TestsUtil.create_table(dynamodb, os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'], external_provider_user_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(dynamodb)

    def test_validation_external_provider_user_who_login_in_invalid_route(self):
        event = {
            'version': '1',
            'region': 'us-east-1',
            'userPoolId': 'us-east-xxxxxxxx',
            'userName': 'external_provider_user',
            'callerContext': {
                'awsSdkVersion': 'aws-sdk-js-2.6.4',
                'clientId': 'xxxxx'
            },
            'triggerSource': 'PreAuthentication_Authentication',
            'request': {
                'userAttributes': {
                    'phone_number': '',
                    'email': 'test@example.com'
                },
                'validationData': {}
            },
            'response': {
                'autoConfirmUser': False,
                'autoVerifyEmail': False,
                'autoVerifyPhone': False
            }
        }
        pre_authentication = PreAuthentication(event=event, context="", dynamodb=dynamodb)
        response = pre_authentication.main()
        self.assertEqual(response['statusCode'], 400)

    def test_external_provider_user_ok_login(self):
        event = {
            'version': '1',
            'region': 'us-east-1',
            'userPoolId': 'us-east-xxxxxxxx',
            'userName': 'external_provider_user',
            'callerContext': {
                'awsSdkVersion': 'aws-sdk-js-2.6.4',
                'clientId': 'xxxxx'
            },
            'triggerSource': 'PreAuthentication_Authentication',
            'request': {
                'userAttributes': {
                    'phone_number': '',
                    'email': 'test@example.com'
                },
                'validationData': {'EXTERNAL_PROVIDER_LOGIN_MARK': 'test_marker'}
            },
            'response': {
                'autoConfirmUser': False,
                'autoVerifyEmail': False,
                'autoVerifyPhone': False
            }
        }
        pre_authentication = PreAuthentication(event=event, context="", dynamodb=dynamodb)
        response = pre_authentication.main()
        self.assertEqual(response, event)

    def test_normal_user_ok_login(self):
        event = {
            'version': '1',
            'region': 'us-east-1',
            'userPoolId': 'us-east-xxxxxxxx',
            'userName': 'normal_user',
            'callerContext': {
                'awsSdkVersion': 'aws-sdk-js-2.6.4',
                'clientId': 'xxxxx'
            },
            'triggerSource': 'PreAuthentication_Authentication',
            'request': {
                'userAttributes': {
                    'email': 'test@example.com'
                },
                'validationData': {}
            },
            'response': {
                'autoConfirmUser': False,
                'autoVerifyEmail': False,
                'autoVerifyPhone': False
            }
        }
        pre_authentication = PreAuthentication(event=event, context="", dynamodb=dynamodb)
        response = pre_authentication.main()
        self.assertEqual(event, response)

    def test_has_user_id_login_ok(self):
        event = {
            'version': '1',
            'region': 'us-east-1',
            'userPoolId': 'us-east-xxxxxxxx',
            'userName': 'user_name',
            'callerContext': {
                'awsSdkVersion': 'aws-sdk-js-2.6.4',
                'clientId': 'xxxxx'
            },
            'triggerSource': 'PreAuthentication_Authentication',
            'request': {
                'userAttributes': {
                    'email': 'test@example.com'
                },
                'validationData': {'EXTERNAL_PROVIDER_LOGIN_MARK': 'test_marker'}
            },
            'response': {
                'autoConfirmUser': False,
                'autoVerifyEmail': False,
                'autoVerifyPhone': False
            }
        }
        pre_authentication = PreAuthentication(event=event, context="", dynamodb=dynamodb)
        response = pre_authentication.main()

        self.assertEqual(event, response)
