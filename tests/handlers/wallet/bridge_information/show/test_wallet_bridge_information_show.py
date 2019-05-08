import json
from unittest import TestCase
from wallet_bridge_information_show import WalletBridgeInformationShow
from unittest.mock import patch, MagicMock


class TestWalletBridgeInformationShow(TestCase):

    @patch(
        'wallet_bridge_information_show.WalletBridgeInformationShow._WalletBridgeInformationShow__get_max_single_relay_amount',
        MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000000002710'))
    @patch(
        'wallet_bridge_information_show.WalletBridgeInformationShow._WalletBridgeInformationShow__get_min_single_relay_amount',
        MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000000000065'))
    @patch('wallet_bridge_information_show.WalletBridgeInformationShow._WalletBridgeInformationShow__get_relay_fee',
           MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000000000064'))
    @patch('wallet_bridge_information_show.WalletBridgeInformationShow._WalletBridgeInformationShow__get_relay_paused',
           MagicMock(return_value='0x0000000000000000000000000000000000000000000000000000000000000000'))
    def test_main_ok(self):
        response = WalletBridgeInformationShow({}, {}).main()

        expected = {
            'max_single_relay_amount': '0x0000000000000000000000000000000000000000000000000000000000002710',
            'min_single_relay_amount': '0x0000000000000000000000000000000000000000000000000000000000000065',
            'relay_fee': '0x0000000000000000000000000000000000000000000000000000000000000064',
            'relay_paused': '0x0000000000000000000000000000000000000000000000000000000000000000'
        }

        self.assertEqual(json.loads(response['body']), expected)
