from web3_util import Web3Util
from unittest import TestCase
from tests_util import TestsUtil
from unittest.mock import patch, MagicMock
from exceptions import Web3ServiceApiError


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


class TestWeb3Util(TestCase):

    def setUp(self):
        TestsUtil.set_all_web3_service_valuables_to_env()

    def tearDown(self):
        pass

    # mock のみのテストとなるため未実施
    def test_create_badge_contract_object(self):
        pass

    @patch('requests.get', MagicMock(return_value=FakeResponse(400, 'test')))
    def test_create_badge_contract_object_with_exception(self):
        with self.assertRaises(Web3ServiceApiError) as e:
            Web3Util.create_badge_contract_object()
        self.assertEqual('test', str(e.exception))

    @patch('web3_util.Web3Util.create_badge_contract_object', MagicMock(return_value=None))
    @patch('requests.get', MagicMock(return_value=FakeResponse(400, 'test')))
    def test_get_badge_types_with_exception(self):
        with self.assertRaises(Web3ServiceApiError) as e:
            Web3Util.get_badge_types('test_user')
        self.assertEqual('test', str(e.exception))

    @patch('web3_util.Web3Util.create_badge_contract_object', MagicMock(return_value=None))
    @patch('requests.get', MagicMock(return_value=FakeResponse(200, '{"hoge": "fuga"}')))
    def test_get_badge_types_not_exists_wallet(self):
        result = Web3Util.get_badge_types('test_user')
        self.assertEqual([], result)

    @patch('requests.get', MagicMock(return_value=FakeResponse(200, '{"public_chain_address": "hoge"}')))
    def test_get_badge_types(self):
        with patch('web3_util.Web3Util.create_badge_contract_object') as mock_contract:
            contract_mock = MagicMock()
            contract_mock.functions.balanceOf().call.return_value = 2
            contract_mock.functions.tokenOfOwnerByIndex().call.return_value = 1
            contract_mock.functions.tokenURI().call.return_value = 'https://example.com/1/metadata.json'
            mock_contract.return_value = contract_mock
            result = Web3Util.get_badge_types('test_user')
            self.assertEqual([1], result)

    @patch('requests.get', MagicMock(return_value=FakeResponse(200, '{"public_chain_address": "hoge"}')))
    def test_get_badge_types_with_multiple(self):
        with patch('web3_util.Web3Util.create_badge_contract_object') as mock_contract:
            contract_mock = MagicMock()
            contract_mock.functions.balanceOf().call.return_value = 2
            contract_mock.functions.tokenOfOwnerByIndex().call.return_value = 1
            contract_mock.functions.tokenURI().call.side_effect = [
                'https://example.com/1/metadata.json',
                'https://example.com/2/metadata.json'
            ]
            mock_contract.return_value = contract_mock
            result = Web3Util.get_badge_types('test_user')
            self.assertEqual([1, 2], result)

    @patch('requests.get', MagicMock(return_value=FakeResponse(200, '{"public_chain_address": "hoge"}')))
    def test_get_badge_types_with_duplicate(self):
        with patch('web3_util.Web3Util.create_badge_contract_object') as mock_contract:
            contract_mock = MagicMock()
            contract_mock.functions.balanceOf().call.return_value = 2
            contract_mock.functions.tokenOfOwnerByIndex().call.return_value = 1
            contract_mock.functions.tokenURI().call.side_effect = [
                'https://example.com/1/metadata.json',
                'https://example.com/2/metadata.json',
                'https://example.com/2/metadata.json'
            ]
            mock_contract.return_value = contract_mock
            result = Web3Util.get_badge_types('test_user')
            self.assertEqual([1, 2], result)

    @patch('requests.get', MagicMock(return_value=FakeResponse(200, '{"public_chain_address": "hoge"}')))
    def test_get_badge_types_not_match(self):
        with patch('web3_util.Web3Util.create_badge_contract_object') as mock_contract:
            contract_mock = MagicMock()
            contract_mock.functions.balanceOf().call.return_value = 1
            contract_mock.functions.tokenOfOwnerByIndex().call.return_value = 1
            contract_mock.functions.tokenURI().call.return_value = 'test'
            mock_contract.return_value = contract_mock
            result = Web3Util.get_badge_types('test_user')
            self.assertEqual([0], result)
