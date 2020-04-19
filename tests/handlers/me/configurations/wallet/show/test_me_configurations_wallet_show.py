import json
import os
from unittest import TestCase
from tests_util import TestsUtil
from me_configurations_wallet_show import MeConfigurationsWalletShow


class TestMeConfigurationsWalletShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()
    test_user_id = 'test-user'
    test_wallet_address = '0xd97464CCB022c05498b9dA894C0B1a0B7562C207'
    test_salt = 'QqKDEbrfoked9BqI+nsiO2qrGcDlc12CenYonbIGauMJSLjcvc8KwYj5VI0C/EozzCHmQW1jynzu7CPqUvUOI3zMB757/2nnqD' \
                'Hy+iUbE1gK23V1f7Tgc+g/VfX7F+8DEwEaTV8lblIRe5qu20VXQ4/z0YemjyR1b4j1lI8NDyM='
    test_encrypted_secret_key = 'U2FsdGVkX19MdIM/Fd97HzivZlRCcafrWIaVufAO0l+YsuThu6TyLyCESaDmtfvCIb1zLHyOoECbEOHSBY' \
                                'j+aNRchX64z42fpjNOOgchR7txP1kqTFPc/2wk/omQDBC3'
    test_signature = '0x3c8e327b2a0a16d10eb7c90739d0abae3325ccce1b13c959f2e915dd9381e25b42c92f5912ce5e0b527ad877203' \
                     '25ca8b3cf90741ed0c5356fb94f75bcdc59181c'

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        # create user_configurations_table
        TestsUtil.create_table(self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'], {})

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def test_main_ok(self):
        item = {
            'user_id': self.test_user_id,
            'private_eth_address': self.test_wallet_address,
            'salt': self.test_salt,
            'encrypted_secret_key': self.test_encrypted_secret_key
        }
        self._set_user_configuration(item)
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.test_user_id
                    }
                }
            }
        }
        response = MeConfigurationsWalletShow(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        expected = {
            'wallet_address': self.test_wallet_address,
            'salt': self.test_salt,
            'encrypted_secret_key': self.test_encrypted_secret_key
        }
        self.assertEqual(expected, json.loads(response['body']))

    def test_main_ok_not_exists_private_eth_address(self):
        item = {
            'user_id': self.test_user_id,
            'mute_users': ['hoge', 'fuga', 'piyo']
        }
        self._set_user_configuration(item)
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.test_user_id
                    }
                }
            }
        }
        response = MeConfigurationsWalletShow(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual({}, json.loads(response['body']))

    def test_main_ok_not_exists_users_configration(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.test_user_id
                    }
                }
            }
        }
        response = MeConfigurationsWalletShow(event=params, context={}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual({}, json.loads(response['body']))

    def _set_user_configuration(self, item):
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        user_configurations_table.put_item(Item=item)
