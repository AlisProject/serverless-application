from user_util import UserUtil
from botocore.exceptions import ClientError
from not_verified_user_error import NotVerifiedUserError
from unittest import TestCase
from unittest.mock import MagicMock
import boto3
import os


class TestUserUtil(TestCase):

    def setUp(self):
        self.cognito = boto3.client('cognito-idp')
        self.dynamodb = boto3.resource('dynamodb')

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

    def test_verified_phone_and_email_ok_not_exist_requestContext(self):
        event = {
        }
        result = UserUtil.verified_phone_and_email(event)
        self.assertTrue(result)

    def test_verified_phone_and_email_ng_not_exist_all_params(self):
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
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

    def test_exists_user_ok(self):
        self.cognito.admin_get_user = MagicMock(return_value='')
        self.assertTrue(UserUtil.exists_user(self.cognito, 'user_pool_id', 'user_id'))

    def test_exists_user_ng(self):
        self.cognito.admin_get_user = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'UserNotFoundException'}},
            'operation_name'
        ))
        self.assertFalse(UserUtil.exists_user(self.cognito, 'user_pool_id', 'user_id'))

    def test_create_sns_user_ok(self):
        self.cognito.admin_create_user = MagicMock(return_value=True)
        self.cognito.admin_initiate_auth = MagicMock(return_value={
            'Session': 'cwefdscx'
        })
        self.cognito.admin_respond_to_auth_challenge = MagicMock(return_value={
            'access_token': 'token'}
        )
        response = UserUtil.create_sns_user(
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

    def test_create_sns_user_ng(self):
        with self.assertRaises(ClientError):
            self.cognito.admin_create_user = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            ))

            UserUtil.create_sns_user(
                self.cognito,
                'user_pool_id',
                'user_pool_app_id',
                'user_id',
                'mail',
                'pass',
                'pass',
                'twitter'
            )

    def test_sns_login_ok(self):
        self.cognito.admin_initiate_auth = MagicMock(return_value={
            'access_token': 'token'
        })
        response = UserUtil.sns_login(
            self.cognito,
            'user_pool_id',
            'user_pool_app_id',
            'user_id',
            'password',
            'twitter')

        self.assertEqual(response['access_token'], 'token')

    def test_sns_login_ng(self):
        with self.assertRaises(ClientError):
            self.cognito.admin_get_user = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'UserNotFoundException'}},
                'operation_name'
            ))
            UserUtil.sns_login(
                self.cognito,
                'user_pool_id',
                'user_pool_app_id',
                'user_id',
                'password',
                'twitter'
            )

    def test_force_non_verified_phone_ok(self):
        self.cognito.admin_update_user_attributes = MagicMock(return_value=True)
        response = UserUtil.force_non_verified_phone(
            self.cognito,
            'user_pool_id',
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
                'user_pool_id',
                'user_id'
            )

    def test_update_user_profile_ok(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.put_item.return_value = True
        response = UserUtil.update_user_profile(
            self.dynamodb,
            'user_id',
            'display_name'
        )

        self.assertEqual(response, None)

    def test_update_user_profile_ng(self):
        with self.assertRaises(ClientError):
            self.dynamodb.Table = MagicMock()
            self.dynamodb.Table.return_value.put_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            UserUtil.update_user_profile(
                self.dynamodb,
                'user_id',
                'display_name'
            )

    def test_add_sns_user_info_ok(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.put_item.return_value = True
        response = UserUtil.add_sns_user_info(
            self.dynamodb,
            'user_id',
            'password'
        )

        self.assertEqual(response, None)

    def test_has_alias_user_id_ok_with_return_true(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.get_item.return_value = {
            'Item': {
                'alias_user_id': 'xxx'
            }
        }
        response = UserUtil.has_alias_user_id(
            self.dynamodb,
            'user_id',
        )

        self.assertTrue(response)

    def test_has_alias_user_id_ok_with_return_false(self):
        self.dynamodb.Table = MagicMock()
        self.dynamodb.Table.return_value.get_item.return_value = {
            'Item': {}
        }
        response = UserUtil.has_alias_user_id(
            self.dynamodb,
            'user_id',
        )

        self.assertFalse(response)

    def test_has_alias_user_id_ng(self):
        with self.assertRaises(ClientError):
            self.dynamodb.Table = MagicMock()
            self.dynamodb.Table.return_value.get_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            UserUtil.has_alias_user_id(
                self.dynamodb,
                'user_id'
            )
