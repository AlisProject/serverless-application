import yaml
import os
import boto3
from unittest import TestCase
from custom_message import CustomMessage
from tests_util import TestsUtil


dynamodb = TestsUtil.get_dynamodb_client()


class TestCustomMessage(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_email_verify(self):
        os.environ['COGNITO_EMAIL_VERIFY_URL'] = "https://alis.example.com/confirm.html"
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'hoge1',
                    'callerContext': {
                        'awsSdkVersion': 'aws-sdk-js-2.6.4',
                        'clientId': 'abcdefghijklmnopqrstuvwxy'
                    },
                    'triggerSource': 'CustomMessage_SignUp',
                    'request': {
                        'userAttributes': {
                            'sub': '12345678-877a-4925-85e1-137c022e8c33',
                            'email_verified': 'false',
                            'cognito:user_status': 'UNCONFIRMED',
                            'phone_number_verified': 'false',
                            'phone_number': '',
                            'email': 'hoge1@example.net'
                        },
                        'codeParameter': '{####}',
                        'usernameParameter': None
                    },
                    'response': {
                        'smsMessage': None,
                        'emailMessage': None,
                        'emailSubject': None
                    }
                }
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        response = custommessage.main()
        self.assertNotEqual(response['response']['emailMessage'], None)

    def test_phone_number_non_japan(self):
        os.environ['COGNITO_EMAIL_VERIFY_URL'] = "https://alis.example.com/confirm.html"
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'hoge2',
                    'callerContext': {
                        'awsSdkVersion': 'aws-sdk-js-2.179.0',
                        'clientId': 'abcdefghijklmnopqrstuvwxy'
                    },
                    'triggerSource': 'CustomMessage_VerifyUserAttribute',
                    'request': {
                        'userAttributes': {
                            'sub': '12345678-2157-480a-8f33-e6945ccb856b',
                            'email_verified': 'true',
                            'cognito:user_status': 'CONFIRMED',
                            'cognito:email_alias': 'hoge3@example.net',
                            'phone_number_verified': 'false',
                            'phone_number': '+448012345678',
                            'email': 'hoge3@example.net'
                        },
                        'codeParameter': '{####}',
                        'usernameParameter': None
                    },
                    'response': {
                        'smsMessage': None,
                        'emailMessage': None,
                        'emailSubject': None
                    }
                }
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        response = custommessage.main()
        self.assertEqual(response['statusCode'],  400)
