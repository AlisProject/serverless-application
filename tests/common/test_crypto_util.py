import os
import boto3
import settings
import base64
from user_util import UserUtil
from crypto_util import CryptoUtil
from unittest import TestCase
from tests_util import TestsUtil


class TestCryptoUtil(TestCase):
    def setUp(self):
        self.cognito = boto3.client('cognito-idp')
        self.dynamodb = TestsUtil.get_dynamodb_client()
        os.environ['COGNITO_USER_POOL_ID'] = 'cognito_user_pool'
        os.environ['LOGIN_SALT'] = '4YGjw4llWxC46bNluUYu1bhaWQgfJjB4'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.external_provider_users_table_items = [
            {
                'external_provider_user_id': 'external_provider_user_id'
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'],
            self.external_provider_users_table_items
        )
        TestsUtil.create_table(self.dynamodb, os.environ['USERS_TABLE_NAME'], [])

    def test_get_external_provider_password_ok(self):
        aes_iv = os.urandom(settings.AES_IV_BYTES)
        encrypted_password = CryptoUtil.encrypt_password('nNU8E9E6OSe9tRQn', aes_iv)
        iv = base64.b64encode(aes_iv).decode()

        UserUtil.add_external_provider_user_info(
            dynamodb=self.dynamodb,
            external_provider_user_id='user_id',
            password=encrypted_password,
            iv=iv,
            email='email'
        )

        password = CryptoUtil.get_external_provider_password(
            self.dynamodb,
            'user_id'
        )
        self.assertEqual(password, 'nNU8E9E6OSe9tRQn')
