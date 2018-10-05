import os
from unittest import TestCase
from pre_authentication import PreAuthentication
from tests_util import TestsUtil

dynamodb = TestsUtil.get_dynamodb_client()


class TestPreAuthentication(TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['LINE_LOGIN_MARK'] = 'test_marker'
        sns_user_items = [
            {'user_id': 'sns_user', 'password': 'password'}
        ]
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)
        TestsUtil.create_table(dynamodb, os.environ['SNS_USERS_TABLE_NAME'], sns_user_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(dynamodb)

    def test_validation_sns_user_who_login_in_invalid_route(self):
        event = {
            'version': '1',
            'region': 'us-east-1',
            'userPoolId': 'us-east-xxxxxxxx',
            'userName': 'sns_user',
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
                'validationData': None
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

    def test_sns_user_ok_login(self):
        event = {
            'version': '1',
            'region': 'us-east-1',
            'userPoolId': 'us-east-xxxxxxxx',
            'userName': 'sns_user',
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
                'validationData': {'THIRD_PARTY_LOGIN': 'test_marker'}
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
