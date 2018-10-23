import os
import json
from unittest import TestCase
from custom_message import CustomMessage
from tests_util import TestsUtil
from jsonschema import validate


dynamodb = TestsUtil.get_dynamodb_client()


class TestCustomMessage(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_email_verify(self):
        os.environ['DOMAIN'] = "alis.example.com"
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
        self.assertRegex(response['response']['emailMessage'], '.*ALISをご利用いただきありがとうございます。.*')
        self.assertEqual(response['response']['emailSubject'], 'Email確認リンク')

    def test_invalid_phone_number(self):
        os.environ['DOMAIN'] = "alis.example.com"
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
                            'phone_number': '',
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
        # 桁が足りない
        event['request']['userAttributes']['phone_number'] = "+810801234567"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        response = custommessage.main()
        self.assertEqual(response['statusCode'],  400)
        # 桁が多い
        event['request']['userAttributes']['phone_number'] = "+81080123456789"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        response = custommessage.main()
        self.assertEqual(response['statusCode'],  400)
        # 日本の番号ではない
        event['request']['userAttributes']['phone_number'] = "+4408012345678"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        response = custommessage.main()
        self.assertEqual(response['statusCode'],  400)
        # 090,080,070,060以外で始まる番号
        event['request']['userAttributes']['phone_number'] = "+8105012345678"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        response = custommessage.main()
        self.assertEqual(response['statusCode'],  400)

    def test_correct_phone_number(self):
        custommessage = CustomMessage(event={}, context="", dynamodb=dynamodb)
        result = validate({'phone_number': '+818012345678'}, custommessage.get_schema())
        self.assertEqual(result,  None)
        result = validate({'phone_number': '+816012345678'}, custommessage.get_schema())
        self.assertEqual(result,  None)

    def test_reset_password(self):
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'resetuser',
                    'callerContext': {
                        'awsSdkVersion': 'aws-sdk-js-2.6.4',
                        'clientId': 'abcdefghijklmnopqrstuvwxy'
                    },
                    'triggerSource': 'CustomMessage_ForgotPassword',
                    'request': {
                        'userAttributes': {
                                'sub': '11111111-2222-3333-4444-555555555555',
                                'email_verified': 'true',
                                'cognito:user_status': 'CONFIRMED',
                                'cognito:email_alias': 'y1@example.net',
                                'phone_number_verified': 'true',
                                'cognito:phone_number_alias': '+818012345678',
                                'phone_number': '+818012345678',
                                'email': 'y1@example.net'
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
        self.assertEqual(response['response']['emailSubject'], 'パスワード再設定コード')
        self.assertEqual(response['response']['emailMessage'], 'resetuserさんのパスワード再設定コードは {####} です')
        self.assertEqual(response['response']['smsMessage'], 'resetuserさんのパスワード再設定コードは {####} です。')

    def test_invalid_line_user_attempt_to_register_phone_number(self):
        os.environ['DOMAIN'] = "alis.example.com"
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'LINE-user',
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
                            'phone_number': '+818011112222',
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
        event['request']['userAttributes']['phone_number'] = "+818011112222"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        response = custommessage.main()
        self.assertEqual(response['statusCode'],  400)
        self.assertEqual(response['body'],
                         json.dumps({"message": "Invalid parameter: This user name is not changed"}))

    def test_invalid_twitter_user_attempt_to_register_phone_number(self):
        os.environ['DOMAIN'] = "alis.example.com"
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'Twitter-user',
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
                            'phone_number': '+818011112222',
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
        self.assertEqual(response['body'],
                         json.dumps({"message": "Invalid parameter: This user name is not changed"}))
