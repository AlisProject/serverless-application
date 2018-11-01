import os
import time
from nonce_util import NonceUtil
from unittest import TestCase
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from tests_util import TestsUtil


class TestNonceUtil(TestCase):
    def setUp(self):
        self.dynamodb = TestsUtil.get_dynamodb_client()
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['NONCE_TABLE_NAME'],
            []
        )

    def test_generate_ok(self):
        nonce = NonceUtil.generate(
            dynamodb=self.dynamodb,
            expiration_minites=15,
            provider='yahoo',
            type='nonce',
            length=10
        )

        table = self.dynamodb.Table(os.environ['NONCE_TABLE_NAME'])
        result = table.get_item(Key={
            'nonce': nonce
        }).get('Item')
        self.assertEqual(len(result), 4)

    def test_generate_ng(self):
        with self.assertRaises(ClientError):
            self.dynamodb.Table = MagicMock()
            self.dynamodb.Table.return_value.put_item.side_effect = ClientError(
                {'Error': {'Code': 'xxxx'}},
                'operation_name'
            )
            NonceUtil.generate(
                dynamodb=self.dynamodb,
                expiration_minites=15,
                provider='yahoo',
                type='nonce',
                length=10
            )

    def test_verify_ok(self):
        table = self.dynamodb.Table(os.environ['NONCE_TABLE_NAME'])
        param = {
            'nonce': 'xxxx',
            'provider': 'test',
            'type': 'test',
            'expiration_time': 1232432234322
        }
        table.put_item(
            Item=param,
            ConditionExpression='attribute_not_exists(nonce)'
        )

        result = NonceUtil.verify(
            dynamodb=self.dynamodb,
            nonce='xxxx',
            provider='test',
            type='test'
        )

        self.assertTrue(result)

    def test_verify_ng_with_do_not_match_nonce(self):
        table = self.dynamodb.Table(os.environ['NONCE_TABLE_NAME'])
        param = {
            'nonce': 'xxxx',
            'provider': 'test',
            'type': 'test',
            'expiration_time': 1232432234322
        }
        table.put_item(
            Item=param,
            ConditionExpression='attribute_not_exists(nonce)'
        )

        result = NonceUtil.verify(
            dynamodb=self.dynamodb,
            nonce='xxx',
            provider='test',
            type='test'
        )

        self.assertFalse(result)

    def test_verify_ng_with_do_not_match_provider(self):
        table = self.dynamodb.Table(os.environ['NONCE_TABLE_NAME'])
        param = {
            'nonce': 'xxxx',
            'provider': 'test',
            'type': 'test',
            'expiration_time': 1232432234322
        }
        table.put_item(
            Item=param,
            ConditionExpression='attribute_not_exists(nonce)'
        )

        result = NonceUtil.verify(
            dynamodb=self.dynamodb,
            nonce='xxxx',
            provider='test1',
            type='test'
        )

        self.assertFalse(result)

    def test_verify_ng_with_do_not_match_type(self):
        table = self.dynamodb.Table(os.environ['NONCE_TABLE_NAME'])
        param = {
            'nonce': 'xxxx',
            'provider': 'test',
            'type': 'test',
            'expiration_time': 1232432234322
        }
        table.put_item(
            Item=param,
            ConditionExpression='attribute_not_exists(nonce)'
        )

        result = NonceUtil.verify(
            dynamodb=self.dynamodb,
            nonce='xxxx',
            provider='test',
            type='test1'
        )

        self.assertFalse(result)
