import json
import os
from unittest import TestCase

from tests_util import TestsUtil

from me_wallet_distributed_tokens_show import MeWalletDistributedTokensShow


class TestMeWalletDistributedTokensShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()

        items = [
            {
                'distribution_id': 'user01-1536184800000000-tip',
                'user_id': 'user01',
                'distribution_type': 'tip',
                'quantity': 10000000000000000000,
                'created_at': 1536184800,
                'sort_key': 1536184800000000
            },
            {
                'distribution_id': 'user01-1524318892000000-like',
                'user_id': 'user01',
                'distribution_type': 'like',
                'quantity': 3000000000000000000,
                'created_at': 1524328892,
                'sort_key': 1524328892000000,
                'evaluated_at': 1524318892000000
            },
            {
                'distribution_id': 'user01-1524318893000000-like',
                'user_id': 'user01',
                'distribution_type': 'like',
                'quantity': 2000000000000000000,
                'created_at': 1524328892,
                'sort_key': 1524328892000000,
                'evaluated_at': 1524318893000000
            },
            {
                'distribution_id': 'user01-1524318892000000-article',
                'user_id': 'user01',
                'distribution_type': 'article',
                'quantity': 6000000000000000000,
                'created_at': 1524328892,
                'sort_key': 1524328892000000,
                'evaluated_at': 1524318892000000
            },
            {
                # 対象のユーザー以外のトークン付与情報
                'distribution_id': 'user02-1524318892000000-article',
                'user_id': 'user02',
                'distribution_type': 'article',
                'quantity': 6000000000000000000,
                'created_at': 1524328892,
                'sort_key': 1524328892000000,
                'evaluated_at': 1524318892000000
            }
        ]

        self.token_distribution_table = self.dynamodb.Table(os.environ['TOKEN_DISTRIBUTION_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['TOKEN_DISTRIBUTION_TABLE_NAME'], items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def test_main_ok(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01'
                    }
                }
            }
        }

        response = MeWalletDistributedTokensShow(params, {}, dynamodb=self.dynamodb).main()

        expected = {
            'article': 6000000000000000000,
            'like': 5000000000000000000,
            'tip': 10000000000000000000,
            'bonus': 0  # DBに存在しなくても0が返却されること
        }

        self.assertTrue(response['statusCode'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected)
