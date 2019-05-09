import os
import settings
from unittest import TestCase
from me_wallet_token_histories_index import MeWalletTokenHistoriesIndex
from unittest.mock import patch
from tests_util import TestsUtil


class TestMeWalletTokenHistoriesIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_aws_auth_to_env()

    def assert_bad_request(self, params):
        target_function = MeWalletTokenHistoriesIndex(params, {}, self.dynamodb, cognito=None)
        response = target_function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        with patch('private_chain_util.PrivateChainUtil.send_transaction') as mock_send_transaction:
            # mock の初期化
            target_range_number = int(settings.HISTORY_RANGE_DAYS * 24 * 60 * 60 / settings.AVERAGE_BLOCK_TIME)
            from_block_number = 1
            return_block_number = hex(from_block_number + target_range_number)
            return_get_timestamp_by_block_number = {"result": {"timestamp": "0x5cb54638"}}
            return_relay_events = {
                "result": [{"hoge": "hoge1"}, {"hoge": "hoge2"}]
            }
            return_apply_relay_events = {
                "result": [{"fuga": "fuga1"}, {"fuga": "fuga2"}, {"fuga": "fuga3"}]
            }
            mock_send_transaction.side_effect = [
                return_block_number,
                return_get_timestamp_by_block_number,
                return_relay_events,
                return_apply_relay_events
            ]

            # テスト対象実施
            private_eth_address = '0x1000000000000000000000000000000000000000'
            event = {
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': 'user_01',
                            'custom:private_eth_address': private_eth_address,
                            'phone_number_verified': 'true',
                            'email_verified': 'true'
                        }
                    }
                }
            }

            response = MeWalletTokenHistoriesIndex(event, {}, self.dynamodb, cognito=None).main()

            # ステータス確認
            self.assertEqual(response['statusCode'], 200)

            # 各種メソッド呼び出し確認
            # send_transaction
            self.assertEqual(len(mock_send_transaction.call_args_list), 4)
            args_block_number = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/block_number',
            }
            self.assertEqual(mock_send_transaction.call_args_list[0][1], args_block_number)
            args_get_block_by_number = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/get_block_by_number',
                'payload_dict': {
                    'block_num': hex(from_block_number)
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[1][1], args_get_block_by_number)
            args_replay_events = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/relay_events',
                'payload_dict': {
                    'from_block': hex(from_block_number),
                    'to_block': return_block_number,
                    'sender_eth_address': private_eth_address[2:]
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[2][1], args_replay_events)
            args_apply_relay_events = {
                'request_url': 'https://' + os.environ[
                    'PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/apply_relay_events',
                'payload_dict': {
                    'from_block': hex(from_block_number),
                    'to_block': return_block_number,
                    'recipient_eth_address': private_eth_address[2:]
                }
            }
            self.assertEqual(mock_send_transaction.call_args_list[3][1], args_apply_relay_events)
