import os
import json
from unittest import TestCase
from login_line_authorize_request import LoginLineAuthorizeRequest
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil
from botocore.exceptions import ClientError

dynamodb = TestsUtil.get_dynamodb_client()


class TestUserUtil(TestCase):
    def setUp(self):
        os.environ['LINE_CHANNEL_ID'] = 'aaaaaaaaaaa'
        os.environ['LINE_CHANNEL_SECRET'] = 'bbbbbbbbbbbbb'
        os.environ['LINE_REDIRECT_URI'] = 'https://xxxxxxx.com'
        os.environ['COGNITO_USER_POOL_ID'] = 'cognito-id'
        os.environ['SNS_LOGIN_COMMON_TEMP_PASSWORD'] = 'Password!'
        os.environ['THIRD_PARTY_LOGIN_MARK'] = 'line'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(dynamodb)

        self.sns_users_table_items = [
            {
                'user_id': 'LINE_U_test_user',
                'user_display_name': 'test_display_name01',
                'email': 'test01@example.com',
                'password': 'test_pass',
                'icon_image_url': 'https://xxxxxxxx'
            },
            {
                'user_id': 'LINE_U_test_user02',
                'user_display_name': 'test_display_name02',
                'email': 'test02@example.com',
                'password': 'test_pass',
                'icon_image_url': 'https://xxxxxxxx',
                'alias_user_id': 'aliasuser'
            }
        ]
        TestsUtil.create_table(dynamodb, os.environ['SNS_USERS_TABLE_NAME'], self.sns_users_table_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(dynamodb)

    @patch("login_line_authorize_request.LoginLineAuthorizeRequest._LoginLineAuthorizeRequest__decode_jwt",
           MagicMock(return_value={
                'sub': 'Uxxxxx',
                'name': 'testuser',
                'picture': 'https://xxxxxxx.png',
                'email': 'test@example.com'
            }))
    def test_main_sign_up_ok(self):
        with patch('login_line_authorize_request.UserUtil') as user_mock, \
             patch('login_line_authorize_request.LoginLineAuthorizeRequest') as line_mock:
            event = {
                'body': {
                    'code': 'testcode',
                }
            }

            event['body'] = json.dumps(event['body'])

            user_mock.exists_user.return_value = False
            user_mock.force_non_verified_phone.return_value = None
            user_mock.wallet_initialization.return_value = None
            user_mock.encrypt_password.return_value = '&yjgFwFeOpd0{0=&y566'
            user_mock.add_sns_user_info.return_value = None
            user_mock.create_sns_user.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }

            line_mock.__get_line_jwt.return_value = 'xxxxxxx'

            response = LoginLineAuthorizeRequest(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'LINE_Uxxxxx',
                    'has_alias_user_id': False,
                    'status': 'sign_up'
                }
            )

    @patch("login_line_authorize_request.LoginLineAuthorizeRequest._LoginLineAuthorizeRequest__decode_jwt",
           MagicMock(return_value={
                'sub': 'U_test_user',
                'name': 'test_display_name01',
                'picture': 'https://xxxxxxx.png',
                'email': 'test01@example.com'
            }))
    def test_main_login_ok(self):
        with patch('login_line_authorize_request.UserUtil') as user_mock, \
             patch('login_line_authorize_request.LoginLineAuthorizeRequest') as line_mock:
            event = {
                'body': {
                    'code': 'testcode',
                }
            }

            event['body'] = json.dumps(event['body'])

            user_mock.exists_user.return_value = True
            user_mock.decrypt_password.return_value = 'password'
            user_mock.sns_login.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            user_mock.has_alias_user_id.return_value = False

            line_mock.__get_line_jwt.return_value = 'xxxxxxx'

            response = LoginLineAuthorizeRequest(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'LINE_U_test_user',
                    'has_alias_user_id': False,
                    'status': 'login'
                }
            )

    @patch("login_line_authorize_request.LoginLineAuthorizeRequest._LoginLineAuthorizeRequest__decode_jwt",
           MagicMock(return_value={
               'sub': 'U_test_user02',
               'name': 'testuser',
               'picture': 'https://xxxxxxx.png',
               'email': 'test@example.com'
           }))
    def test_main_login_ok_with_alias(self):
        with patch('login_line_authorize_request.UserUtil') as user_mock, \
             patch('login_line_authorize_request.LoginLineAuthorizeRequest') as line_mock:
            event = {
                'body': {
                    'code': 'testcode',
                }
            }

            event['body'] = json.dumps(event['body'])

            user_mock.exists_user.return_value = True
            user_mock.decrypt_password.return_value = 'password'
            user_mock.sns_login.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'aaaaa',
                    'IdToken': 'bbbbb',
                    'RefreshToken': 'ccccc'
                }
            }
            user_mock.has_alias_user_id.return_value = True

            line_mock.__get_line_jwt.return_value = 'xxxxxxx'

            response = LoginLineAuthorizeRequest(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'access_token': 'aaaaa',
                    'id_token': 'bbbbb',
                    'refresh_token': 'ccccc',
                    'last_auth_user': 'aliasuser',
                    'has_alias_user_id': True,
                    'status': 'login'
                }
            )

    @patch("login_line_authorize_request.LoginLineAuthorizeRequest._LoginLineAuthorizeRequest__decode_jwt",
           MagicMock(return_value={
                'sub': 'Uxxxxx',
                'name': 'testuser',
                'picture': 'https://xxxxxxx.png',
                'email': 'test@example.com'
            }))
    def test_main_sign_up_with_exception(self):
        with patch('login_line_authorize_request.UserUtil') as user_mock, \
             patch('login_line_authorize_request.LoginLineAuthorizeRequest') as line_mock:
            event = {
                'body': {
                    'code': 'testcode',
                }
            }

            event['body'] = json.dumps(event['body'])
            user_mock.exists_user.return_value = False
            user_mock.create_sns_user.side_effect = ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            )
            user_mock.force_non_verified_phone.return_value = None
            user_mock.update_user_profile.return_value = None
            user_mock.add_sns_user_info.return_value = None
            user_mock.has_alias_user_id.return_value = True

            line_mock.__get_line_jwt.return_value = 'xxxxxxx'

            response = LoginLineAuthorizeRequest(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )

    @patch("login_line_authorize_request.LoginLineAuthorizeRequest._LoginLineAuthorizeRequest__decode_jwt",
           MagicMock(return_value={
                'sub': 'U_test_user',
                'name': 'test_display_name01',
                'picture': 'https://xxxxxxx.png',
                'email': 'test01@example.com'
            }))
    def test_main_login_with_exception(self):
        with patch('login_line_authorize_request.UserUtil') as user_mock, \
             patch('login_line_authorize_request.LoginLineAuthorizeRequest') as line_mock:
            event = {
                'body': {
                    'code': 'testcode',
                }
            }

            event['body'] = json.dumps(event['body'])

            user_mock.exists_user.return_value = True
            user_mock.decrypt_password.return_value = 'password'
            user_mock.sns_login.side_effect = ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            )
            user_mock.has_alias_user_id.return_value = False

            line_mock.__get_line_jwt.return_value = 'xxxxxxx'

            response = LoginLineAuthorizeRequest(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 500)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'Internal server error'
                }
            )

    @patch("login_line_authorize_request.LoginLineAuthorizeRequest._LoginLineAuthorizeRequest__decode_jwt",
           MagicMock(return_value={
                'sub': 'Uxxxxx',
                'name': 'testuser',
                'picture': 'https://xxxxxxx.png',
                'email': 'test@example.com'
            }))
    def test_main_sign_up_with_email_check_exception(self):
        with patch('login_line_authorize_request.UserUtil') as user_mock, \
             patch('login_line_authorize_request.LoginLineAuthorizeRequest') as line_mock:
            event = {
                'body': {
                    'code': 'testcode',
                }
            }

            event['body'] = json.dumps(event['body'])
            user_mock.exists_user.return_value = False
            user_mock.create_sns_user.side_effect = ClientError(
                {'Error': {'Code': 'UsernameExistsException'}},
                'operation_name'
            )
            user_mock.force_non_verified_phone.return_value = None
            user_mock.update_user_profile.return_value = None
            user_mock.add_sns_user_info.return_value = None
            user_mock.has_alias_user_id.return_value = False

            line_mock.__get_line_jwt.return_value = 'xxxxxxx'

            response = LoginLineAuthorizeRequest(event=event, context="", dynamodb=dynamodb).main()
            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(
                json.loads(response['body']),
                {
                    'message': 'An account with the email already exists.'
                }
            )
