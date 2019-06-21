import os
from unittest import TestCase
from custom_message import CustomMessage
from tests_util import TestsUtil
from jsonschema import validate
from unittest.mock import patch, MagicMock

dynamodb = TestsUtil.get_dynamodb_client()


class TestCustomMessage(TestCase):

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_aws_auth_to_env()
        TestsUtil.set_all_tables_name_to_env()
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        TestsUtil.delete_all_tables(dynamodb)
        external_provider_user_items = [
            {
                'external_provider_user_id': 'external_provider_user_id',
                'password': 'password',
                'user_id': 'external_provider_user'
            }
        ]
        TestsUtil.create_table(dynamodb, os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'], external_provider_user_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(dynamodb)

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
        self.assertEqual(response['response']['emailSubject'], '【ALIS】登録のご案内：メールアドレスの確認')

    @patch('private_chain_util.PrivateChainUtil.send_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000000000000'))
    def test_main_ok_get_verification_code_for_phone_number_first_time(self):
        with patch('custom_message.boto3.client') as mock:
            cognito_mock = MagicMock()
            cognito_mock.user_list = MagicMock(return_value=[])
            mock.return_value = cognito_mock
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
                        'triggerSource': 'CustomMessage_VerifyUserAttribute',
                        'request': {
                            'userAttributes': {
                                'sub': '12345678-877a-4925-85e1-137c022e8c33',
                                'email_verified': 'true',
                                'cognito:user_status': 'UNCONFIRMED',
                                'phone_number_verified': 'false',
                                'phone_number': '+819000001234',
                                'email': 'hoge1@example.net',
                                'custom:private_eth_address': '0xaaaa'
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
            custom_message = CustomMessage(event=event, context="", dynamodb=dynamodb)
            response = custom_message.main()
            self.assertRegex(response['response']['smsMessage'],
                             'ALISです。\n' + event['userName'] + 'さんの認証コードは {####} です。.*')
            self.assertRegex(response['response']['emailMessage'], '.*ALISをご利用いただきありがとうございます。.*')
            self.assertEqual(response['response']['emailSubject'], '【ALIS】登録のご案内：メールアドレスの確認')

    @patch('private_chain_util.PrivateChainUtil.send_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000000000000'))
    def test_main_ok_get_verification_code_for_phone_number_already_confirmed(self):
        with patch('custom_message.boto3.client') as mock:
            cognito_mock = MagicMock()
            cognito_mock.user_list = MagicMock(return_value=[])
            mock.return_value = cognito_mock
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
                        'triggerSource': 'CustomMessage_VerifyUserAttribute',
                        'request': {
                            'userAttributes': {
                                'sub': '12345678-877a-4925-85e1-137c022e8c33',
                                'email_verified': 'true',
                                'cognito:user_status': 'UNCONFIRMED',
                                'phone_number_verified': 'true',
                                'phone_number': '+819000001234',
                                'email': 'hoge1@example.net',
                                'custom:private_eth_address': '0xaaaa'
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
            custom_message = CustomMessage(event=event, context="", dynamodb=dynamodb)
            response = custom_message.main()
            self.assertRegex(response['response']['smsMessage'],
                             'ALISです。\n' + event['userName'] + 'さんの認証コードは {####} です。.*')
            self.assertRegex(response['response']['emailMessage'], '.*ALISをご利用いただきありがとうございます。.*')
            self.assertEqual(response['response']['emailSubject'], '【ALIS】登録のご案内：メールアドレスの確認')

    @patch('private_chain_util.PrivateChainUtil.send_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000011111111'))
    def test_main_ok_get_verification_code_for_phone_number_already_confirmed_with_exists_token(self):
        with patch('custom_message.boto3.client') as mock:
            cognito_mock = MagicMock()
            cognito_mock.user_list = MagicMock(return_value=[])
            mock.return_value = cognito_mock
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
                        'triggerSource': 'CustomMessage_VerifyUserAttribute',
                        'request': {
                            'userAttributes': {
                                'sub': '12345678-877a-4925-85e1-137c022e8c33',
                                'email_verified': 'true',
                                'cognito:user_status': 'UNCONFIRMED',
                                'phone_number_verified': 'true',
                                'phone_number': '+819000001234',
                                'email': 'hoge1@example.net',
                                'custom:private_eth_address': '0xaaaa'
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
            custom_message = CustomMessage(event=event, context="", dynamodb=dynamodb)
            response = custom_message.main()
            self.assertRegex(response['response']['smsMessage'],
                             'ALISです。\n' + event['userName'] + 'さんの認証コードは {####} です。.*')
            self.assertRegex(response['response']['emailMessage'], '.*ALISをご利用いただきありがとうございます。.*')
            self.assertEqual(response['response']['emailSubject'], '【ALIS】登録のご案内：メールアドレスの確認')

    @patch('private_chain_util.PrivateChainUtil.send_transaction',
           MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000011111111'))
    def test_main_ng_get_verification_code_after_updated_phone_number_with_exists_token(self):
        with patch('custom_message.boto3.client') as mock:
            cognito_mock = MagicMock()
            cognito_mock.user_list = MagicMock(return_value=[])
            mock.return_value = cognito_mock
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
                        'triggerSource': 'CustomMessage_VerifyUserAttribute',
                        'request': {
                            'userAttributes': {
                                'sub': '12345678-877a-4925-85e1-137c022e8c33',
                                'email_verified': 'true',
                                'cognito:user_status': 'UNCONFIRMED',
                                'phone_number_verified': 'false',
                                'phone_number': '+819000001234',
                                'email': 'hoge1@example.net',
                                'custom:private_eth_address': '0xaaaa'
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
            custom_message = CustomMessage(event=event, context="", dynamodb=dynamodb)
            with self.assertRaises(Exception) as e:
                custom_message.main()
            self.assertEqual('Do not allow phone number updates', str(e.exception))

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
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("'+810801234567' does not match '^\\\\+81[6-9]0\\\\d{8}$'", str(e.exception))
        # 桁が多い
        event['request']['userAttributes']['phone_number'] = "+81080123456789"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("'+81080123456789' is too long", str(e.exception))
        # 日本の番号ではない
        event['request']['userAttributes']['phone_number'] = "+440801234567"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("'+440801234567' does not match '^\\\\+81[6-9]0\\\\d{8}$'", str(e.exception))
        # 090,080,070,060以外で始まる番号
        event['request']['userAttributes']['phone_number'] = "+810501234567"
        custommessage = CustomMessage(event=event, context="", dynamodb=dynamodb)
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("'+810501234567' does not match '^\\\\+81[6-9]0\\\\d{8}$'", str(e.exception))

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
        self.assertEqual(response['response']['emailSubject'], '【ALIS】パスワードの変更：再設定コードの送付')
        self.assertEqual(response['response']['emailMessage'], 'resetuserさんのパスワード再設定コードは {####} です')
        self.assertEqual(response['response']['smsMessage'], 'resetuserさんのパスワード再設定コードは {####} です。')

    def test_reset_password_ng_with_external_provider_user(self):
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'external_provider_user',
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
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("external provider's user can not execute", str(e.exception))

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
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("external provider's user can not execute", str(e.exception))

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
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("external provider's user can not execute", str(e.exception))

    def test_invalid_yahoo_user_attempt_to_register_phone_number(self):
        os.environ['DOMAIN'] = "alis.example.com"
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'Yahoo-user',
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
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("external provider's user can not execute", str(e.exception))

    def test_invalid_facebook_user_attempt_to_register_phone_number(self):
        os.environ['DOMAIN'] = "alis.example.com"
        event = {
                    'version': '1',
                    'region': 'us-east-1',
                    'userPoolId': 'us-east-1_xxxxxxxxx',
                    'userName': 'Facebook-user',
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
        with self.assertRaises(Exception) as e:
            custommessage.main()
        self.assertEqual("external provider's user can not execute", str(e.exception))
