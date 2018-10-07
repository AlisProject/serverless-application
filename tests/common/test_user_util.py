import os
import boto3
from user_util import UserUtil
from not_verified_user_error import NotVerifiedUserError
from unittest import TestCase
from unittest.mock import MagicMock
from botocore.exceptions import ClientError


class TestUserUtil(TestCase):
    def setUp(self):
        self.cognito = boto3.client('cognito-idp')
        self.dynamodb = boto3.resource('dynamodb')
        os.environ['COGNITO_USER_POOL_ID'] = 'cognito_user_pool'

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

    def test_delete_sns_id_cognito_user_ok(self):
        self.cognito.admin_delete_user = MagicMock(return_value=True)
        user_id = 'testuser'
        self.assertEqual(UserUtil.delete_sns_id_cognito_user(self.cognito, user_id), True)

    def test_delete_sns_id_cognito_user_not_found(self):
        self.cognito.admin_delete_user = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'UserNotFoundException'}},
                'operation_code'
            ))
        user_id = 'testuser'
        self.assertFalse(UserUtil.delete_sns_id_cognito_user(self.cognito, user_id))

    def test_add_alias_to_sns_user_ok(self):
        self.dynamodb.update_item = MagicMock(return_value=None)
        response = UserUtil.add_alias_to_sns_user(
            'alias_id',
            self.dynamodb,
            'user_id'
        )
        self.assertEqual(response, None)

    def test_add_alias_to_sns_user_ng(self):
        self.dynamodb.update_item = MagicMock(side_effect=ClientError(
                {'Error': {'Code': 'xxxxxx'}},
                'operation_name'
            ))
        response = UserUtil.add_alias_to_sns_user(
            'alias_id',
            self.dynamodb,
            'user_id'
        )
        self.assertEqual(response['statusCode'], 500)


