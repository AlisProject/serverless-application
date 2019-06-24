import os
import boto3
from user_util import UserUtil
from not_verified_user_error import NotVerifiedUserError
from unittest import TestCase
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from tests_util import TestsUtil


class TestUserUtil(TestCase):
    def setUp(self):
        self.cognito = boto3.client('cognito-idp')
        self.dynamodb = TestsUtil.get_dynamodb_client()
        os.environ['COGNITO_USER_POOL_ID'] = 'cognito_user_pool'
        os.environ['LOGIN_SALT'] = '4YGjw4llWxC46bNluUYu1bhaWQgfJjB4'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.external_provider_users_table_items = [
            {
                'external_provider_user_id': 'external_provider_user_id',
                'user_id': 'user_id'
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'],
            self.external_provider_users_table_items
        )
        TestsUtil.create_table(self.dynamodb, os.environ['USERS_TABLE_NAME'], [])

    def test_verified_phone_and_email_ok(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        result = UserUtil.verified_phone_and_email(event)
        self.assertTrue(result)

    def test_verified_phone_and_email_ng_not_exist_phone(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'email_verified': 'true'
                    }
                }
            }
        }
        with self.assertRaises(NotVerifiedUserError):
            UserUtil.verified_phone_and_email(event)

    def test_verified_phone_and_email_ng_not_exist_email(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'phone_number_verified': 'true'
                    }
                }
            }
        }
        with self.assertRaises(NotVerifiedUserError):
            UserUtil.verified_phone_and_email(event)

    def test_verified_phone_and_email_ng_phone_false(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'phone_number_verified': 'false',
                        'email_verified': 'true'
                    }
                }
            }
        }
        with self.assertRaises(NotVerifiedUserError):
            UserUtil.verified_phone_and_email(event)

    def test_verified_phone_and_email_ng_email_false(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'phone_number_verified': 'true',
                        'email_verified': 'false'
                    }
                }
            }
        }
        with self.assertRaises(NotVerifiedUserError):
            UserUtil.verified_phone_and_email(event)

    def test_verified_phone_and_email_ng_all_params_false(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'phone_number_verified': 'false',
                        'email_verified': 'false'
                    }
                }
            }
        }
        with self.assertRaises(NotVerifiedUserError):
            UserUtil.verified_phone_and_email(event)

    def test_force_non_verified_phone_ok(self):
        self.cognito.admin_update_user_attributes = MagicMock(return_value=True)
        response = UserUtil.force_non_verified_phone(
            self.cognito,
            'user_id'
        )
        self.assertEqual(response, None)

    def test_force_non_verified_phone_ng(self):
        with self.assertRaises(ClientError):
            self.cognito.admin_update_user_attributes = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            ))
            UserUtil.force_non_verified_phone(
                self.cognito,
                'user_id'
            )

    def test_delete_external_provider_id_cognito_user_ok(self):
        self.cognito.admin_delete_user = MagicMock(return_value=True)
        user_id = 'testuser'
        self.assertEqual(UserUtil.delete_external_provider_id_cognito_user(self.cognito, user_id), True)

    def test_delete_external_provider_id_cognito_user_not_found(self):
        self.cognito.admin_delete_user = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'UserNotFoundException'}},
                'operation_code'
            ))
        user_id = 'testuser'
        self.assertFalse(UserUtil.delete_external_provider_id_cognito_user(self.cognito, user_id))

    def test_add_user_id_to_external_provider_user_ok(self):
        self.dynamodb.update_item = MagicMock(return_value=None)
        response = UserUtil.add_user_id_to_external_provider_user(
            'user_id',
            self.dynamodb,
            'external_provider_user_id'
        )
        self.assertEqual(response, None)

    def test_add_user_id_to_external_provider_user_ng(self):
        self.dynamodb.update_item = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            ))
        response = UserUtil.add_user_id_to_external_provider_user(
            'user_id',
            self.dynamodb,
            'external_provider_user_id'
        )
        self.assertEqual(response['statusCode'], 500)

    def test_exists_user_ok(self):
        self.assertTrue(UserUtil.exists_user(self.dynamodb, 'external_provider_user_id'))

    def test_exists_user_ng(self):
        self.assertFalse(UserUtil.exists_user(self.dynamodb, 'test-user'))

    def test_is_external_provider_user_ok(self):
        self.assertTrue(UserUtil.is_external_provider_user(self.dynamodb, 'user_id'))

    def test_is_external_provider_user_ng(self):
        self.assertFalse(UserUtil.is_external_provider_user(self.dynamodb, 'test-user'))

    def test_create_external_provider_user_ok(self):
        self.cognito.admin_create_user = MagicMock(return_value=True)
        self.cognito.admin_initiate_auth = MagicMock(return_value={
            'Session': 'cwefdscx'
        })
        self.cognito.admin_respond_to_auth_challenge = MagicMock(return_value={
            'access_token': 'token'}
        )
        response = UserUtil.create_external_provider_user(
            self.cognito,
            'user_pool_id',
            'user_pool_app_id',
            'user_id',
            'mail',
            'pass',
            'pass',
            'twitter'
        )
        self.assertEqual(response['access_token'], 'token')

    def test_create_external_provider_user_ng(self):
        with self.assertRaises(ClientError):
            self.cognito.admin_create_user = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            ))
            UserUtil.create_external_provider_user(
                self.cognito,
                'user_pool_id',
                'user_pool_app_id',
                'user_id',
                'mail',
                'pass',
                'pass',
                'twitter'
            )

    def test_external_provider_login_ok(self):
        self.cognito.admin_initiate_auth = MagicMock(return_value={
            'access_token': 'token'
        })
        response = UserUtil.external_provider_login(
            self.cognito,
            'user_pool_id',
            'user_pool_app_id',
            'user_id',
            'password',
            'twitter')
        self.assertEqual(response['access_token'], 'token')

    def test_external_provider_login_ng(self):
        with self.assertRaises(ClientError):
            self.cognito.admin_get_user = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'UserNotFoundException'}},
                'operation_name'
            ))
            UserUtil.external_provider_login(
                self.cognito,
                'user_pool_id',
                'user_pool_app_id',
                'user_id',
                'password',
                'twitter'
            )

    def test_add_external_provider_user_info_ok(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.put_item.return_value = True
        response = UserUtil.add_external_provider_user_info(
            self.dynamodb,
            'external_provider_user_id',
            'password',
            'iv',
            'email'
        )
        self.assertEqual(response, None)

    def test_add_external_provider_user_info_ng(self):
        with self.assertRaises(ClientError):
            self.dynamodb.Table = MagicMock()
            self.dynamodb.Table.return_value.put_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            UserUtil.add_external_provider_user_info(
                self.dynamodb,
                'external_provider_user_id',
                'password',
                'iv',
                'email'
            )

    def test_has_user_id_ok_with_return_true(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.get_item.return_value = {
            'Item': {
                'user_id': 'xxx'
            }
        }
        response = UserUtil.has_user_id(
            self.dynamodb,
            'external_provider_user_id',
        )
        self.assertTrue(response)

    def test_get_user_id_ok(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.get_item.return_value = {
            'Item': {
                'user_id': 'you_are_external_provider_user'
            }
        }
        response = UserUtil.get_user_id(
            self.dynamodb,
            'external_provider_user_id',
        )
        self.assertEqual(response, 'you_are_external_provider_user')

    def test_get_user_id_ng(self):
        with self.assertRaises(ClientError):
            self.dynamodb.Table = MagicMock()
            self.dynamodb.Table.return_value.get_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            UserUtil.get_user_id(
                self.dynamodb,
                'external_provider_user_id',
            )

    def test_has_user_id_ok_with_return_false(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.get_item.return_value = {
            'Item': {}
        }
        response = UserUtil.has_user_id(
            self.dynamodb,
            'external_provider_user_id',
        )
        self.assertFalse(response)

    def test_has_user_id_ng(self):
        with self.assertRaises(ClientError):
            self.dynamodb.Table = MagicMock()
            self.dynamodb.Table.return_value.get_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            UserUtil.has_user_id(
                self.dynamodb,
                'external_provider_user_id'
            )

    def test_check_try_to_register_as_yahoo_user_ng(self):
        self.assertTrue(UserUtil.check_try_to_register_as_yahoo_user('Yahoo-xxxxxxx'))

    def test_check_try_to_register_as_yahoo_user_ok(self):
        self.assertFalse(UserUtil.check_try_to_register_as_yahoo_user('myuser'))
        self.assertFalse(UserUtil.check_try_to_register_as_yahoo_user('myuser-Yahoo-xxxxxxx'))

    def test_check_try_to_register_as_facebook_user_ng(self):
        self.assertTrue(UserUtil.check_try_to_register_as_facebook_user('Facebook-xxxxxxx'))

    def test_check_try_to_register_as_facebook_user_ok(self):
        self.assertFalse(UserUtil.check_try_to_register_as_facebook_user('myuser'))
        self.assertFalse(UserUtil.check_try_to_register_as_facebook_user('myuser-Facebook-xxxxxxx'))

    def test_check_try_to_register_as_twitter_user_ng(self):
        self.assertTrue(UserUtil.check_try_to_register_as_twitter_user('Twitter-xxxxxxx'))

    def test_check_try_to_register_as_twitter_user_ok(self):
        self.assertFalse(UserUtil.check_try_to_register_as_twitter_user('myuser'))
        self.assertFalse(UserUtil.check_try_to_register_as_twitter_user('myuser-Twitter-xxxxxxx'))

    def test_check_try_to_register_as_line_user_ok(self):
        self.assertFalse(UserUtil.check_try_to_register_as_line_user('myuser'))
        self.assertFalse(UserUtil.check_try_to_register_as_line_user('myuser-LiNe-xxxxxxx'))

    def test_check_try_to_register_as_line_user_ng(self):
        self.assertTrue(UserUtil.check_try_to_register_as_line_user('LINE-user'))

    def test_wallet_initialization_ok(self):
        os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'] = 'test'
        os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'] = 'test'
        os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] = 'test'
        with patch('user_util.requests.post') as requests_mock, patch('user_util.AWSRequestsAuth') as aws_auth_mock:
            requests_mock.return_value = PrivateChainApiFakeResponse(
                status_code=200,
                text='{"result":"my_address"}'
            )
            aws_auth_mock.return_value = True
            self.cognito.admin_update_user_attributes = MagicMock(
                return_value=True)
            UserUtil.wallet_initialization(
                self.cognito,
                'user_pool_id',
                'user_id'
            )
            self.cognito.admin_update_user_attributes.assert_called_once_with(
                UserAttributes=[
                    {
                        'Name': 'custom:private_eth_address',
                        'Value': 'my_address'
                    }
                ],
                UserPoolId='user_pool_id',
                Username='user_id'
            )

    def test_add_user_profile_ok(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.put_item.return_value = True
        response = UserUtil.add_user_profile(
            self.dynamodb,
            'user_id',
            'display_name'
        )

        self.assertEqual(response, None)

    def test_add_user_profile_ng(self):
        with self.assertRaises(ClientError):
            self.dynamodb.Table = MagicMock()
            self.dynamodb.Table.return_value.put_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            UserUtil.add_user_profile(
                self.dynamodb,
                'user_id',
                'display_name'
            )


class PrivateChainApiFakeResponse:
    def __init__(self, status_code, text=''):
        self._status_code = status_code
        self._text = text

    def get_status_code(self):
        return self._status_code

    def get_text(self):
        return self._text
    status_code = property(get_status_code)
    text = property(get_text)
