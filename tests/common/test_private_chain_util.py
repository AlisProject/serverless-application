import settings
import os
from tests_util import TestsUtil
from private_chain_util import PrivateChainUtil
from web3 import Web3, HTTPProvider
from eth_account.messages import encode_defunct
from eth_keys.exceptions import BadSignature
from jsonschema import ValidationError
from unittest import TestCase
from unittest.mock import MagicMock, patch
from exceptions import SendTransactionError, ReceiptError


class FakeResponse:
    def __init__(self, status_code, text=''):
        self._status_code = status_code
        self._text = text

    def get_status_code(self):
        return self._status_code

    def get_text(self):
        return self._text

    status_code = property(get_status_code)
    text = property(get_text)


class TestPrivateChainUtil(TestCase):
    @classmethod
    def setUpClass(cls):
        TestsUtil.set_aws_auth_to_env()
        TestsUtil.set_all_private_chain_valuables_to_env()

    @patch('requests.post', MagicMock(return_value=FakeResponse(status_code=200, text='{"result": "result_str"}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    def test_send_transaction_ok(self):
        url = 'test_url'
        response = PrivateChainUtil.send_transaction(request_url=url)
        self.assertEqual(response, 'result_str')

    @patch('requests.post', MagicMock(return_value=FakeResponse(status_code=200, text='{"result": "result_str"}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    def test_send_transaction_ok_with_payload(self):
        url = 'test_url'
        payload_dict = {'key': 'value'}
        response = PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload_dict)
        self.assertEqual(response, 'result_str')

    @patch('requests.post', MagicMock(return_value=FakeResponse(status_code=500, text='{"result": "result_str"}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    def test_send_transaction_ng_status_code_not_200(self):
        with self.assertRaises(SendTransactionError):
            url = 'test_url'
            PrivateChainUtil.send_transaction(request_url=url)

    @patch('requests.post', MagicMock(return_value=FakeResponse(status_code=200, text='{"error": "error"}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    def test_send_transaction_ng_exists_error(self):
        with self.assertRaises(SendTransactionError):
            url = 'test_url'
            PrivateChainUtil.send_transaction(request_url=url)

    def test_send_raw_transaction_ok(self):
        test_raw_transaction = '0xabcdef0123456789'
        test_url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/send_raw_transaction'
        magic_lib = MagicMock(return_value='0x10')
        with patch('private_chain_util.PrivateChainUtil.send_transaction', magic_lib):
            result = PrivateChainUtil.send_raw_transaction(test_raw_transaction)
            self.assertEqual('0x10', result)

            _, kwargs = magic_lib.call_args
            expect_payload = {
                'raw_transaction': test_raw_transaction
            }
            self.assertEqual(test_url, kwargs['request_url'])
            self.assertEqual(expect_payload, kwargs['payload_dict'])

    @patch('requests.post',
           MagicMock(return_value=FakeResponse(status_code=200, text='{"result": {"logs": [{"type": "mined"}]}}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    def test_is_transaction_completed_ok(self):
        tran = '0x1234567890123456789012345678901234567890'
        response = PrivateChainUtil.is_transaction_completed(transaction=tran)
        self.assertEqual(response, True)

    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ok_last(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{"result": {"logs": [{"type": "mined"}]}}')
            ]
            tran = '0x1234567890123456789012345678901234567890'
            response = PrivateChainUtil.is_transaction_completed(transaction=tran)
            self.assertEqual(response, True)
            self.assertEqual(mock_post.call_count, settings.TRANSACTION_CONFIRM_COUNT)

    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ok_multiple_logs(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{"result": {"logs": [{"type": "mined"}, {"type": "mined"}]}}')
            ]
            tran = '0x1234567890123456789012345678901234567890'
            response = PrivateChainUtil.is_transaction_completed(transaction=tran)
            self.assertEqual(response, True)
            self.assertEqual(mock_post.call_count, settings.TRANSACTION_CONFIRM_COUNT)

    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_count_over(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{}'),
                FakeResponse(status_code=200, text='{"result": {"logs": [{"type": "mined"}]}}')
            ]
            tran = '0x1234567890123456789012345678901234567890'
            response = PrivateChainUtil.is_transaction_completed(transaction=tran)
            self.assertEqual(response, False)
            self.assertEqual(mock_post.call_count, settings.TRANSACTION_CONFIRM_COUNT)

    @patch('requests.post',
           MagicMock(return_value=FakeResponse(status_code=200, text='{"test": ""}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_not_exists_result(self):
        tran = '0x1234567890123456789012345678901234567890'
        response = PrivateChainUtil.is_transaction_completed(transaction=tran)
        self.assertEqual(response, False)

    @patch('requests.post',
           MagicMock(return_value=FakeResponse(status_code=200, text='{"result": {}}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_not_exists_result_value(self):
        with self.assertRaises(ReceiptError):
            tran = '0x1234567890123456789012345678901234567890'
            PrivateChainUtil.is_transaction_completed(transaction=tran)

    @patch('requests.post',
           MagicMock(return_value=FakeResponse(status_code=200, text='{"result": {"test": [{"type": "mined"}]}}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_not_exists_logs(self):
        with self.assertRaises(ReceiptError):
            tran = '0x1234567890123456789012345678901234567890'
            PrivateChainUtil.is_transaction_completed(transaction=tran)

    @patch('requests.post',
           MagicMock(return_value=FakeResponse(status_code=200, text='{"result": {"logs": [{"type": "dummy"}]}}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_not_exists_mined_type(self):
        with self.assertRaises(ReceiptError):
            tran = '0x1234567890123456789012345678901234567890'
            PrivateChainUtil.is_transaction_completed(transaction=tran)

    @patch('requests.post', MagicMock(return_value=FakeResponse(
        status_code=200, text='{"result": {"logs": [{"type": "mined"}, {"type": "dummy"}]}}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_exists_not_mined_type(self):
        with self.assertRaises(ReceiptError):
            tran = '0x1234567890123456789012345678901234567890'
            PrivateChainUtil.is_transaction_completed(transaction=tran)

    def test_get_balance_ok(self):
        test_address = '0x401BA17D89D795B3C6e373c5062F1C3F8979e73B'
        test_url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/balance'
        test_balance = 0x10
        magic_lib = MagicMock(return_value=test_balance)
        with patch('private_chain_util.PrivateChainUtil.send_transaction', magic_lib):
            result = PrivateChainUtil.get_balance(test_address)
            self.assertEqual(test_balance, result)

            _, kwargs = magic_lib.call_args
            expect_payload = {
                'private_eth_address': test_address[2:]
            }
            self.assertEqual(test_url, kwargs['request_url'])
            self.assertEqual(expect_payload, kwargs['payload_dict'])

    def test_get_transaction_count_ok(self):
        test_address = '0x401BA17D89D795B3C6e373c5062F1C3F8979e73B'
        test_url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/get_transaction_count'
        test_count = '0x10'
        magic_lib = MagicMock(return_value=test_count)
        with patch('private_chain_util.PrivateChainUtil.send_transaction', magic_lib):
            result = PrivateChainUtil.get_transaction_count(test_address)
            self.assertEqual(test_count, result)

            _, kwargs = magic_lib.call_args
            expect_payload = {
                'from_user_eth_address': test_address
            }
            self.assertEqual(test_url, kwargs['request_url'])
            self.assertEqual(expect_payload, kwargs['payload_dict'])

    def test_increment_transaction_count_ok(self):
        result = PrivateChainUtil.increment_transaction_count('0x0')
        self.assertEqual('0x1', result)

        result = PrivateChainUtil.increment_transaction_count('0xf')
        self.assertEqual('0x10', result)

    def test_get_allowance_ok(self):
        test_address = '0x401BA17D89D795B3C6e373c5062F1C3F8979e73B'
        test_url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/allowance'
        test_allowance = '0x10'
        magic_lib = MagicMock(return_value=test_allowance)
        with patch('private_chain_util.PrivateChainUtil.send_transaction', magic_lib):
            result = PrivateChainUtil.get_allowance(test_address)
            self.assertEqual(test_allowance, result)

            _, kwargs = magic_lib.call_args
            expect_payload = {
                'from_user_eth_address': test_address,
                'owner_eth_address': test_address[2:],
                'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
            }
            self.assertEqual(test_url, kwargs['request_url'])
            self.assertEqual(expect_payload, kwargs['payload_dict'])

    def test_validate_message_signature_ok(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_message = 'hogepiyo'
        sign_message = web3.eth.account.sign_message(
            encode_defunct(text=test_message),
            private_key=test_account.key.hex()
        )
        # 例外が発生しないこと
        PrivateChainUtil.validate_message_signature(
            test_message,
            sign_message['signature'].hex(),
            test_account.address
        )

    def test_validate_message_signature_ng(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_message = 'hogepiyo'
        failure_signature = '0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef' \
                            '0123456789abcdef0123456789abcdef0123456789ab'
        with self.assertRaises(BadSignature) as e:
            PrivateChainUtil.validate_message_signature(
                test_message,
                failure_signature,
                test_account.address
            )
        self.assertEqual(e.exception.args[0], 'Invalid signature')

    def test_validate_raw_transaction_signature_ok(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        transaction = {
            'to': '0xF0109fC8DF283027b6285cc889F5aA624EaC1F55',
            'value': 1000000000,
            'gas': 2000000,
            'gasPrice': 234567897654321,
            'nonce': 0,
            'chainId': 1
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        # 例外が発生しないこと
        PrivateChainUtil.validate_raw_transaction_signature(signed.rawTransaction.hex(), test_account.address)

    def test_validate_raw_transaction_signature_ng(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        transaction = {
            'to': '0xF0109fC8DF283027b6285cc889F5aA624EaC1F55',
            'value': 1000000000,
            'gas': 2000000,
            'gasPrice': 234567897654321,
            'nonce': 0,
            'chainId': 1
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        failure_address = '0x123456789a123456789a123456789a123456789a'
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_raw_transaction_signature(
                signed.rawTransaction.hex(),
                failure_address
            )
        self.assertEqual(e.exception.args[0], 'Signature is invalid')

    def test_get_data_from_raw_transaction_ok(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xa9059cbb'
        nonce = 10
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 0,
            'to': web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': test_data,
            'chainId': 8995
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        actual = PrivateChainUtil.get_data_from_raw_transaction(signed.rawTransaction.hex(), format(nonce, '#x'))
        self.assertEqual(test_data[2:], actual)

    def test_get_data_from_raw_transaction_ok_with_relay_method(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xeeec0e24'
        nonce = 10
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 0,
            'to': web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS']),
            'value': 0,
            'data': test_data,
            'chainId': 8995
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        actual = PrivateChainUtil.get_data_from_raw_transaction(
            signed.rawTransaction.hex(),
            format(nonce, '#x')
        )
        self.assertEqual(test_data[2:], actual)

    def test_get_data_from_raw_transaction_ng_failure_nonce(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xa9059cbb'
        nonce = 10
        transaction = {
            'nonce': nonce + 1,
            'gasPrice': 0,
            'gas': 0,
            'to': web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': test_data,
            'chainId': 8995
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.get_data_from_raw_transaction(signed.rawTransaction.hex(), format(nonce, '#x'))
        self.assertEqual(e.exception.args[0], 'nonce is invalid')

    def test_get_data_from_raw_transaction_ng_failure_gasPrice(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xa9059cbb'
        nonce = 10
        transaction = {
            'nonce': nonce,
            'gas': 0,
            'gasPrice': 1,
            'to': web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': test_data,
            'chainId': 8995
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.get_data_from_raw_transaction(signed.rawTransaction.hex(), format(nonce, '#x'))
        self.assertEqual(e.exception.args[0], 'gasPrice is invalid')

    def test_get_data_from_raw_transaction_ng_failure_gasLimit(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xa9059cbb'
        nonce = 10
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 1,
            'to': web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': test_data,
            'chainId': 8995
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.get_data_from_raw_transaction(signed.rawTransaction.hex(), format(nonce, '#x'))
        self.assertEqual(e.exception.args[0], 'gasLimit is invalid')

    def test_get_data_from_raw_transaction_ng_failure_to(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xa9059cbb'
        nonce = 10
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 0,
            'to': test_account.address,
            'value': 0,
            'data': test_data,
            'chainId': 8995
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.get_data_from_raw_transaction(signed.rawTransaction.hex(), format(nonce, '#x'))
        self.assertEqual(e.exception.args[0], 'private_chain_alis_token_address is invalid')

    def test_get_data_from_raw_transaction_ng_failure_value(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xa9059cbb'
        nonce = 10
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 0,
            'to': web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 1,
            'data': test_data,
            'chainId': 8995
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.get_data_from_raw_transaction(signed.rawTransaction.hex(), format(nonce, '#x'))
        self.assertEqual(e.exception.args[0], 'value is invalid')

    def test_get_data_from_raw_transaction_ng_failure_v(self):
        web3 = Web3(HTTPProvider('http://localhost:8584'))
        test_account = web3.eth.account.create()
        test_data = '0xa9059cbb'
        nonce = 10
        transaction = {
            'nonce': nonce,
            'gasPrice': 0,
            'gas': 0,
            'to': web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']),
            'value': 0,
            'data': test_data,
            'chainId': 8994
        }
        signed = web3.eth.account.sign_transaction(transaction, test_account.key)
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.get_data_from_raw_transaction(signed.rawTransaction.hex(), format(nonce, '#x'))
        self.assertEqual(e.exception.args[0], 'v is invalid')

    def test_get_data_from_raw_transaction_ng_failure_raw_transaction(self):
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.get_data_from_raw_transaction('0xabcdef', '0x10')
        self.assertEqual(e.exception.args[0], 'raw_transaction is invalid')

    def test_validate_erc20_transfer_data_ok_tip_value_minimum(self):
        method = 'a9059cbb'
        to_address = format(10, '064x')
        tip_value = format(1, '064x')
        test_tx = method + to_address + tip_value
        # 例外が発生しないこと
        # 引数で利用する to_address は先頭に 0x が付き、かつ40文字想定なので '0x' + to_address[24:] のように修正している
        PrivateChainUtil.validate_erc20_transfer_data(test_tx, '0x' + to_address[24:])

    def test_validate_erc20_transfer_data_ok_tip_value_maximum(self):
        method = 'a9059cbb'
        to_address = format(10, '064x')
        tip_value = format(10 ** 24, '064x')
        test_tx = method + to_address + tip_value
        # 例外が発生しないこと
        # 引数で利用する to_address は先頭に 0x が付き、かつ40文字想定なので '0x' + to_address[24:] のように修正している
        PrivateChainUtil.validate_erc20_transfer_data(test_tx, '0x' + to_address[24:])

    def test_validate_erc20_transfer_data_ng_data(self):
        method = 'a9059cbb'
        to_address = format(10, '064x')
        tip_value = format(100, '064x')
        test_tx = method + to_address + tip_value + 'a'
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_transfer_data(test_tx, '0x' + to_address[24:])
        self.assertEqual(e.exception.args[0], 'data is invalid')

    def test_validate_erc20_transfer_data_ng_method(self):
        method = 'aaaaaaaa'
        to_address = format(10, '064x')
        tip_value = format(100, '064x')
        test_tx = method + to_address + tip_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_transfer_data(test_tx, '0x' + to_address[24:])
        self.assertEqual(e.exception.args[0], 'method is invalid')

    def test_validate_erc20_transfer_data_ng_to_address(self):
        method = 'a9059cbb'
        to_address = format(10, '064x')
        tip_value = format(100, '064x')
        test_tx = method + to_address + tip_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_transfer_data(test_tx, '0xabcdef')
        self.assertEqual(e.exception.args[0], 'to_address is invalid')

    def test_validate_erc20_transfer_data_ng_tip_value_less_than_minimum(self):
        method = 'a9059cbb'
        to_address = format(10, '064x')
        tip_value = format(0, '064x')
        test_tx = method + to_address + tip_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_transfer_data(test_tx, '0x' + to_address[24:])
        self.assertEqual(e.exception.args[0], '0 is less than the minimum of 1')

    def test_validate_erc20_transfer_data_ng_tip_value_greater_than_maximum(self):
        method = 'a9059cbb'
        to_address = format(10, '064x')
        tip_value = format(10 ** 24 + 1, '064x')
        test_tx = method + to_address + tip_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_transfer_data(test_tx, '0x' + to_address[24:])
        self.assertEqual(
            e.exception.args[0],
            '1000000000000000000000001 is greater than the maximum of 1000000000000000000000000'
        )

    def test_validate_erc20_approve_data_ok_token_send_value_minimum(self):
        method = '095ea7b3'
        spender_eth_address = format(0, '024x') + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        token_send_value = format(1000000000000000000, '064x')
        test_tx = method + spender_eth_address + token_send_value
        # 例外が発生しないこと
        # 引数で利用する spender_eth_address は先頭に 0x が付き、かつ40文字想定なので '0x' + spender_eth_address[24:] のように修正している
        PrivateChainUtil.validate_erc20_approve_data(test_tx)

    def test_validate_erc20_approve_data_ok_token_send_value_maximum(self):
        method = '095ea7b3'
        spender_eth_address = format(0, '024x') + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        token_send_value = format(10 ** 24, '064x')
        test_tx = method + spender_eth_address + token_send_value
        # 例外が発生しないこと
        # 引数で利用する spender_eth_address は先頭に 0x が付き、かつ40文字想定なので '0x' + spender_eth_address[24:] のように修正している
        PrivateChainUtil.validate_erc20_approve_data(test_tx)

    def test_validate_erc20_approve_data_ok_token_send_value_zero(self):
        method = '095ea7b3'
        spender_eth_address = format(0, '024x') + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        token_send_value = format(0, '064x')
        test_tx = method + spender_eth_address + token_send_value
        # 例外が発生しないこと
        # 引数で利用する spender_eth_address は先頭に 0x が付き、かつ40文字想定なので '0x' + spender_eth_address[24:] のように修正している
        PrivateChainUtil.validate_erc20_approve_data(test_tx)

    def test_validate_erc20_approve_data_ng_data(self):
        method = '095ea7b3'
        spender_eth_address = format(0, '024x') + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        token_send_value = format(100, '064x')
        test_tx = method + spender_eth_address + token_send_value + 'a'
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_approve_data(test_tx)
        self.assertEqual(e.exception.args[0], 'data is invalid')

    def test_validate_erc20_approve_data_ng_method(self):
        method = 'aaaaaaaa'
        spender_eth_address = format(0, '024x') + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        token_send_value = format(100, '064x')
        test_tx = method + spender_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_approve_data(test_tx)
        self.assertEqual(e.exception.args[0], 'method is invalid')

    def test_validate_erc20_approve_data_ng_spender_eth_address(self):
        method = '095ea7b3'
        spender_eth_address = format(10, '064x')
        token_send_value = format(100, '064x')
        test_tx = method + spender_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_approve_data(test_tx)
        self.assertEqual(e.exception.args[0], 'spender_eth_address is invalid')

    def test_validate_erc20_approve_data_ng_token_send_value_less_than_minimum(self):
        method = '095ea7b3'
        spender_eth_address = format(0, '024x') + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        token_send_value = format(1000000000000000000 - 1, '064x')
        test_tx = method + spender_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_approve_data(test_tx)
        self.assertEqual(e.exception.args[0], '999999999999999999 is less than the minimum of 1000000000000000000')

    def test_validate_erc20_approve_data_ng_token_send_value_greater_than_maximum(self):
        method = '095ea7b3'
        spender_eth_address = format(0, '024x') + os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        token_send_value = format(10 ** 24 + 1, '064x')
        test_tx = method + spender_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_approve_data(test_tx)
        self.assertEqual(
            e.exception.args[0],
            '1000000000000000000000001 is greater than the maximum of 1000000000000000000000000'
        )

    def test_validate_erc20_relay_data_ok_token_send_value_minimum(self):
        method = 'eeec0e24'
        recipient_eth_address = format(10, '064x')
        token_send_value = format(1000000000000000000, '064x')
        test_tx = method + recipient_eth_address + token_send_value
        # 例外が発生しないこと
        # 引数で利用する recipient_eth_address は先頭に 0x が付き、かつ40文字想定なので '0x' + recipient_eth_address[24:] のように修正している
        PrivateChainUtil.validate_erc20_relay_data(test_tx)

    def test_validate_erc20_relay_data_ok_token_send_value_maximum(self):
        method = 'eeec0e24'
        recipient_eth_address = format(10, '064x')
        token_send_value = format(10 ** 24, '064x')
        test_tx = method + recipient_eth_address + token_send_value
        # 例外が発生しないこと
        # 引数で利用する recipient_eth_address は先頭に 0x が付き、かつ40文字想定なので '0x' + recipient_eth_address[24:] のように修正している
        PrivateChainUtil.validate_erc20_relay_data(test_tx)

    def test_validate_erc20_relay_data_ng_data(self):
        method = 'eeec0e24'
        recipient_eth_address = format(10, '064x')
        token_send_value = format(100, '064x')
        test_tx = method + recipient_eth_address + token_send_value + 'a'
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_relay_data(test_tx)
        self.assertEqual(e.exception.args[0], 'data is invalid')

    def test_validate_erc20_relay_data_ng_method(self):
        method = 'aaaaaaaa'
        recipient_eth_address = format(10, '064x')
        token_send_value = format(100, '064x')
        test_tx = method + recipient_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_relay_data(test_tx)
        self.assertEqual(e.exception.args[0], 'method is invalid')

    def test_validate_erc20_relay_data_ng_recipient_eth_address(self):
        method = 'eeec0e24'
        recipient_eth_address = 'z' + format(10, '063x')
        token_send_value = format(100, '064x')
        test_tx = method + recipient_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_relay_data(test_tx)
        self.assertEqual(e.exception.args[0], 'recipient_eth_address is invalid')

    def test_validate_erc20_relay_data_ng_token_send_value_less_than_minimum(self):
        method = 'eeec0e24'
        recipient_eth_address = format(10, '064x')
        token_send_value = format(1000000000000000000 - 1, '064x')
        test_tx = method + recipient_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_relay_data(test_tx)
        self.assertEqual(e.exception.args[0], '999999999999999999 is less than the minimum of 1000000000000000000')

    def test_validate_erc20_relay_data_ng_token_send_value_greater_than_maximum(self):
        method = 'eeec0e24'
        recipient_eth_address = format(10, '064x')
        token_send_value = format(10 ** 24 + 1, '064x')
        test_tx = method + recipient_eth_address + token_send_value
        with self.assertRaises(ValidationError) as e:
            PrivateChainUtil.validate_erc20_relay_data(test_tx)
        self.assertEqual(
            e.exception.args[0],
            '1000000000000000000000001 is greater than the maximum of 1000000000000000000000000'
        )
