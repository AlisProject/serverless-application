import json
import os
import boto3
import re
from unittest import TestCase
from unittest.mock import MagicMock, patch
from tests_util import TestsUtil
from web3 import Web3, HTTPProvider
from me_configurations_wallet_add import MeConfigurationsWalletAdd
from eth_account.messages import encode_defunct


class TestMeConfigurationsWalletAdd(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls) -> None:
        TestsUtil.set_aws_auth_to_env()
        TestsUtil.set_all_private_chain_valuables_to_env()
        os.environ['COGNITO_USER_POOL_ID'] = 'cognito_user_pool'
        cls.web3 = Web3(HTTPProvider('http://localhost:8584'))
        cls.test_account = cls.web3.eth.account.create()

    def setUp(self):
        self.cognito = boto3.client('cognito-idp')
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.user_configurations_items = [
            {
                'user_id': 'exists-user',
                'private_eth_address': '0x1234567890123456789012345678901234567890',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth'
            },
            {
                'user_id': 'exists-user2',
                'mute_users': {'mute-user-00', 'mute-user-01'}
            }
        ]
        TestsUtil.create_table(
            self.dynamodb, os.environ['USER_CONFIGURATIONS_TABLE_NAME'], self.user_configurations_items
        )

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, event):
        response = MeConfigurationsWalletAdd(event, {}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_ok_not_exists_old_private_eth_address(self):
        test_user = 'test-user'
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        test_signature = self.create_singed_message_transactions(test_user)

        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'salt': test_salt,
                'encrypted_secret_key': test_key,
                'signature': test_signature,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])
        self.cognito.admin_update_user_attributes = MagicMock(return_value=True)
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'private_eth_address': self.test_account.address,
            'salt': test_salt,
            'encrypted_secret_key': test_key
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)
        self.cognito.admin_update_user_attributes.assert_called_once_with(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=test_user,
            UserAttributes=[
                {
                    'Name': 'custom:private_eth_address',
                    'Value': self.test_account.address
                }
            ]
        )

    def test_main_ok_exists_old_private_eth_address(self):
        test_user = 'test-user'
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        test_signature = self.create_singed_message_transactions(test_user)
        old_address = '0x1234567890123456789012345678901234567890'

        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'salt': test_salt,
                'encrypted_secret_key': test_key,
                'signature': test_signature,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user,
                        'custom:private_eth_address': old_address
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])
        self.cognito.admin_update_user_attributes = MagicMock(return_value=True)
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'private_eth_address': self.test_account.address,
            'old_private_eth_address': self.user_configurations_items[0]['private_eth_address'],
            'salt': test_salt,
            'encrypted_secret_key': test_key
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)
        self.cognito.admin_update_user_attributes.assert_called_once_with(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=test_user,
            UserAttributes=[
                {
                    'Name': 'custom:private_eth_address',
                    'Value': self.test_account.address
                }
            ]
        )

    def test_main_ok_exists_user_configurations(self):
        test_user = self.user_configurations_items[1]['user_id']
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        test_signature = self.create_singed_message_transactions(test_user)

        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'salt': test_salt,
                'encrypted_secret_key': test_key,
                'signature': test_signature,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])
        self.cognito.admin_update_user_attributes = MagicMock(return_value=True)
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        expected = {
            'user_id': test_user,
            'mute_users': {'mute-user-00', 'mute-user-01'},
            'private_eth_address': self.test_account.address,
            'salt': test_salt,
            'encrypted_secret_key': test_key
        }
        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)
        self.cognito.admin_update_user_attributes.assert_called_once_with(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=test_user,
            UserAttributes=[
                {
                    'Name': 'custom:private_eth_address',
                    'Value': self.test_account.address
                }
            ]
        )

    def test_main_ng_exists_private_eth_address(self):
        test_user = self.user_configurations_items[0]['user_id']
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        test_signature = self.create_singed_message_transactions(test_user)

        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'salt': test_salt,
                'encrypted_secret_key': test_key,
                'signature': test_signature,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '{"message": "Invalid parameter: private_eth_address is exists."}')
        # user_configurations が書き換わっていないこと
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        actual = user_configurations_table.get_item(Key={'user_id': test_user})['Item']
        self.assertEqual(self.user_configurations_items[0], actual)

    def test_main_ok_call_validate_method(self):
        test_user = 'test-user'
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        test_signature = self.create_singed_message_transactions(test_user)

        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'salt': test_salt,
                'encrypted_secret_key': test_key,
                'signature': test_signature,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])

        with patch('private_chain_util.PrivateChainUtil.validate_message_signature') as mock_validate_message_signature:
            self.cognito.admin_update_user_attributes = MagicMock(return_value=True)
            response = MeConfigurationsWalletAdd(
                event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
            ).main()

            args, _ = mock_validate_message_signature.call_args
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(test_user, args[0])
            self.assertEqual(test_signature, args[1])
            self.assertEqual(self.test_account.address, args[2])

    def test_main_ng_not_specified_wallet_address(self):
        test_user = self.user_configurations_items[0]['user_id']
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        test_signature = self.create_singed_message_transactions(test_user)

        event = {
            'body': {
                'salt': test_salt,
                'encrypted_secret_key': test_key,
                'signature': test_signature,
            }
        }
        event['body'] = json.dumps(event['body'])
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(
            re.match('{"message": "Invalid parameter: \'wallet_address\' is a required property', response['body'])
        )

    def test_main_ng_not_specified_salt(self):
        test_user = self.user_configurations_items[0]['user_id']
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        test_signature = self.create_singed_message_transactions(test_user)

        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'encrypted_secret_key': test_key,
                'signature': test_signature,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(
            re.match('{"message": "Invalid parameter: \'salt\' is a required property', response['body'])
        )

    def test_main_ng_not_specified_encrypted_secret_key(self):
        test_user = self.user_configurations_items[0]['user_id']
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_signature = self.create_singed_message_transactions(test_user)

        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'salt': test_salt,
                'signature': test_signature,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(
            re.match(
                '{"message": "Invalid parameter: \'encrypted_secret_key\' is a required property',
                response['body']
            )
        )

    def test_main_ng_not_specified_signature(self):
        test_user = self.user_configurations_items[0]['user_id']
        test_salt = 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7HYaj' \
                    'j7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o='
        test_key = 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmWCLeQqBvELM1uYR3xoH1WZ0p' \
                   'GwKH/+haa6sbtkVYQ3P/iERp/HKzth'
        event = {
            'body': {
                'wallet_address': self.test_account.address,
                'salt': test_salt,
                'encrypted_secret_key': test_key,
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': test_user
                    }
                }
            }
        }
        event['body'] = json.dumps(event['body'])
        response = MeConfigurationsWalletAdd(
            event=event, context={}, dynamodb=self.dynamodb, cognito=self.cognito
        ).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertIsNotNone(
            re.match(
                '{"message": "Invalid parameter: \'signature\' is a required property',
                response['body']
            )
        )

    def test_validation_wallet_address_required(self):
        event = {
            'body': {
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_salt_required(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7caC',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_encrypted_secret_key_required(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7caC',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_signature_required(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7caC',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_wallet_address_less_than_min(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7ca',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_wallet_address_greater_than_max(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7caCa',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_wallet_address_use_invalid_char(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64eZzZZ',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_salt_use_invalid_char(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7caC',
                'salt': '###N10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_encrypted_secret_key_use_invalid_char(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7caC',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': '###sdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xbd5170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def test_validation_signature_use_invalid_char(self):
        event = {
            'body': {
                'wallet_address': '0x9b51333FD7E78b6792bA441C04b4331ee64e7caC',
                'salt': 'EesN10uxbFLuaQcqdzPQeJeGk2L4Aazt9EfIoDX/murBtwrnGNulIzB2DP7hW/OLFpHXyqJ2kksJ5L6iBsjPfAEaHl7'
                        'HYajj7cF3pNbBJFp3ggOxIEhD7AxEmKEfLSv2n8P7EQbxGGdrsib+I2kl32jTOKXh/5+syd0v3VE197o=',
                'encrypted_secret_key': 'U2FsdGVkX1/LlsoLIXoWe7naw/7p9EQONzluugwwI/TM1nZgVXSLeeDjZ/R0qd3wNv+Teg5ckmW'
                                        'CLeQqBvELM1uYR3xoH1WZ0pGwKH/+haa6sbtkVYQ3P/iERp/HKzth',
                'signature': '0xzzz170dbe99fa15b9369eec05eb5a31e94cad38163a7c22d5cc4fae4849075807da13eadbcc450a24ff9'
                             'da9fc2e0c47e07d471753733ed6423f1b0bf13353ee21c'
            },
        }
        event['body'] = json.dumps(event['body'])
        self.assert_bad_request(event)

    def create_singed_message_transactions(self, user_id):
        return self.web3.eth.account.sign_message(
            encode_defunct(text=user_id),
            private_key=self.test_account.key
        )['signature'].hex()
