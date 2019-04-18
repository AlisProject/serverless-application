# -*- coding: utf-8 -*-
from wallet_bridge_information_show import WalletBridgeInformationShow


def lambda_handler(event, context):
    wallet_bridge_information_show = WalletBridgeInformationShow(event, context)
    return wallet_bridge_information_show.main()
