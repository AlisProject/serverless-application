import settings
from tests_util import TestsUtil
from private_chain_util import PrivateChainUtil
from unittest import TestCase
from unittest.mock import MagicMock, patch
from exceptions import SendTransactionError


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

    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_multiple_ng_pattern(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [
                FakeResponse(status_code=200, text='{"hoge": {"fuga": []}}'),
                FakeResponse(status_code=200, text='{"result": {"hoge": []}}'),
                FakeResponse(status_code=200, text='{"result": {"logs": []}}'),
                FakeResponse(status_code=200, text='{"result": {"logs": [{"hoge": "fuga"}]}}'),
                FakeResponse(status_code=200, text='{"result": {"logs": [{"type": "mined"},{"hoge": "fuga"}]}}'),
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
           MagicMock(return_value=FakeResponse(status_code=200, text='{"result": {"test": [{"type": "mined"}]}}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_not_exists_logs(self):
        tran = '0x1234567890123456789012345678901234567890'
        response = PrivateChainUtil.is_transaction_completed(transaction=tran)
        self.assertEqual(response, False)

    @patch('requests.post',
           MagicMock(return_value=FakeResponse(status_code=200, text='{"result": {"logs": [{"type": "dummy"}]}}')))
    @patch('aws_requests_auth.aws_auth.AWSRequestsAuth', MagicMock(return_value='dummy'))
    @patch('time.sleep', MagicMock(return_value=''))
    def test_is_transaction_completed_ng_not_exists_mined_type(self):
        tran = '0x1234567890123456789012345678901234567890'
        response = PrivateChainUtil.is_transaction_completed(transaction=tran)
        self.assertEqual(response, False)
